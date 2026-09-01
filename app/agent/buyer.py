"""
AI Buyer Agent: interprets natural-language shopping requests and translates
them into structured commerce tool calls.

Supports two modes:
1. LLM-powered (when LLM_API_KEY is configured) - uses OpenAI-compatible API
2. Rule-based fallback - keyword extraction for demo without API key
"""
import re
import uuid
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from app.config import settings
from app.agent.tools import CommerceToolkit


@dataclass
class AgentStep:
    """Represents one step in the agent's execution pipeline."""
    step_number: int
    tool_name: str
    description: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, success, error


@dataclass
class AgentResult:
    """Complete result of an agent shopping session."""
    session_id: str
    user_request: str
    steps: List[AgentStep] = field(default_factory=list)
    final_summary: str = ""
    success: bool = False


class AIBuyer:
    """Demo AI buyer that processes natural-language shopping requests."""

    def __init__(self, base_url: str = None):
        self.session_id = f"agent_{uuid.uuid4().hex[:8]}"
        self.toolkit = CommerceToolkit(self.session_id, base_url=base_url)

    def process_request(self, user_request: str) -> AgentResult:
        """Process a natural-language shopping request end-to-end."""
        result = AgentResult(
            session_id=self.session_id,
            user_request=user_request,
        )

        if settings.llm_enabled:
            return self._llm_process(user_request, result)
        else:
            return self._rule_based_process(user_request, result)

    def _rule_based_process(self, request: str, result: AgentResult) -> AgentResult:
        """Rule-based NL parser for demo. Handles Hindi-English mixed queries."""
        parsed = self._parse_intent(request)

        step_num = 1

        # Step 1: Search products
        search_params = {}
        if parsed.get("query"):
            search_params["query"] = parsed["query"]
        if parsed.get("category"):
            search_params["category"] = parsed["category"]
        if parsed.get("max_price"):
            search_params["max_price"] = parsed["max_price"]
        if parsed.get("min_price"):
            search_params["min_price"] = parsed["min_price"]
        if parsed.get("color"):
            search_params["color"] = parsed["color"]
        if parsed.get("brand"):
            search_params["brand"] = parsed["brand"]

        if not search_params:
            search_params["query"] = request

        step = AgentStep(step_num, "search_products",
                         f"Searching for products matching: {search_params}",
                         search_params)
        search_result = self.toolkit.search_products(**search_params)
        step.output_data = search_result
        step.status = "success" if search_result.get("success") else "error"
        result.steps.append(step)
        step_num += 1

        if not search_result.get("success"):
            result.final_summary = f"Search failed: {search_result.get('error', 'Unknown error')}"
            return result

        products = search_result.get("data", {}).get("products", [])
        if not products:
            result.final_summary = "No products found matching your request. Try different search terms."
            return result

        # Step 2: Get product details (pick best match)
        selected = products[0]
        product_id = selected["product_id"]

        step = AgentStep(step_num, "get_product",
                         f"Getting details for: {selected['name']}",
                         {"product_id": product_id})
        product_result = self.toolkit.get_product(product_id)
        step.output_data = product_result
        step.status = "success" if product_result.get("success") else "error"
        result.steps.append(step)
        step_num += 1

        # Step 3: Check stock
        step = AgentStep(step_num, "check_stock",
                         f"Checking availability for: {selected['name']}",
                         {"product_id": product_id})
        stock_result = self.toolkit.check_stock(product_id)
        step.output_data = stock_result
        step.status = "success" if stock_result.get("success") else "error"
        result.steps.append(step)
        step_num += 1

        stock_data = stock_result.get("data", {})
        if not stock_data.get("available", False):
            result.final_summary = f"Sorry, '{selected['name']}' is currently out of stock."
            result.success = False
            return result

        # Check if user wants to buy/cart/checkout
        wants_purchase = parsed.get("action") in ("buy", "cart", "checkout", "order")

        if not wants_purchase:
            # Just show results
            result.final_summary = (
                f"Found {len(products)} product(s). Top match: {selected['name']} "
                f"at ₹{selected['price']}. {stock_data.get('message', '')} "
                f"Say 'add to cart' or 'buy' to proceed with purchase."
            )
            result.success = True
            return result

        # Step 4: Create cart
        step = AgentStep(step_num, "create_cart",
                         "Creating a shopping cart",
                         {"session_id": self.session_id})
        cart_result = self.toolkit.create_cart()
        step.output_data = cart_result
        step.status = "success" if cart_result.get("success") else "error"
        result.steps.append(step)
        step_num += 1

        if not cart_result.get("success"):
            result.final_summary = f"Failed to create cart: {cart_result.get('error')}"
            return result

        cart_id = cart_result["data"]["cart_id"]
        quantity = parsed.get("quantity", 1)

        # Step 5: Add to cart
        step = AgentStep(step_num, "add_to_cart",
                         f"Adding {quantity}x {selected['name']} to cart",
                         {"cart_id": cart_id, "product_id": product_id, "quantity": quantity})
        add_result = self.toolkit.add_to_cart(cart_id, product_id, quantity)
        step.output_data = add_result
        step.status = "success" if add_result.get("success") else "error"
        result.steps.append(step)
        step_num += 1

        if not add_result.get("success"):
            result.final_summary = f"Failed to add to cart: {add_result.get('error')}"
            return result

        # Step 6: Create order
        step = AgentStep(step_num, "create_order",
                         "Creating order from cart",
                         {"cart_id": cart_id, "session_id": self.session_id})
        order_result = self.toolkit.create_order(cart_id)
        step.output_data = order_result
        step.status = "success" if order_result.get("success") else "error"
        result.steps.append(step)
        step_num += 1

        if not order_result.get("success"):
            result.final_summary = f"Failed to create order: {order_result.get('error')}"
            return result

        order_id = order_result["data"]["order_id"]
        total = order_result["data"]["total_amount"]

        # Step 7: Create checkout
        step = AgentStep(step_num, "create_checkout",
                         f"Initiating payment for ₹{total}",
                         {"order_id": order_id})
        checkout_result = self.toolkit.create_checkout(order_id)
        step.output_data = checkout_result
        step.status = "success" if checkout_result.get("success") else "error"
        result.steps.append(step)

        if checkout_result.get("success"):
            checkout_data = checkout_result["data"]
            result.final_summary = (
                f"Order placed successfully!\n"
                f"• Product: {selected['name']}\n"
                f"• Quantity: {quantity}\n"
                f"• Total: ₹{total}\n"
                f"• Order ID: {order_id}\n"
                f"• Payment Status: {checkout_data.get('status', 'pending')}\n"
                f"• Payment Mode: {checkout_data.get('payment_mode', 'N/A')}"
            )
            result.success = True
        else:
            result.final_summary = f"Order created but checkout failed: {checkout_result.get('error')}"

        return result

    def _parse_intent(self, text: str) -> Dict[str, Any]:
        """Parse natural-language shopping request into structured intent."""
        text_lower = text.lower().strip()
        parsed = {}

        # --- Action detection ---
        buy_keywords = ["buy", "kharid", "checkout", "order", "add to cart",
                        "cart me", "cart mein", "lelo", "le lo", "purchase",
                        "book", "mangwa", "chahiye"]
        for kw in buy_keywords:
            if kw in text_lower:
                parsed["action"] = "buy"
                break
        if "action" not in parsed:
            search_keywords = ["show", "dikhao", "dikha", "search", "find",
                               "looking for", "dhundh", "batao"]
            for kw in search_keywords:
                if kw in text_lower:
                    parsed["action"] = "search"
                    break
        if "action" not in parsed:
            parsed["action"] = "search"

        # --- Price extraction ---
        price_patterns = [
            r"(?:under|below|less than|max|upto|up to|ke andar|se kam|tak)\s*(?:rs\.?|₹|inr)?\s*(\d+)",
            r"(?:rs\.?|₹|inr)\s*(\d+)\s*(?:ke andar|se kam|tak|under|below|less)",
            r"(\d+)\s*(?:ke andar|se kam|tak|rupee|rs)",
            r"(?:under|below)\s*(\d+)",
            r"(?:budget|price)\s*(?:is)?\s*(?:rs\.?|₹)?\s*(\d+)",
        ]
        for pattern in price_patterns:
            match = re.search(pattern, text_lower)
            if match:
                parsed["max_price"] = float(match.group(1))
                break

        # Min price
        min_patterns = [
            r"(?:above|over|more than|min|at least|se upar|se zyada)\s*(?:rs\.?|₹|inr)?\s*(\d+)",
        ]
        for pattern in min_patterns:
            match = re.search(pattern, text_lower)
            if match:
                parsed["min_price"] = float(match.group(1))
                break

        # --- Color extraction ---
        colors = ["black", "white", "blue", "red", "green", "grey", "gray",
                  "navy", "pink", "brown", "beige", "maroon", "olive", "teal",
                  "cream", "gold", "silver", "tan", "multicolor", "yellow", "orange"]
        # Hindi colors
        hindi_colors = {"neela": "blue", "kala": "black", "safed": "white",
                        "laal": "red", "hara": "green", "peela": "yellow",
                        "gulabi": "pink", "bhura": "brown"}
        for hindi, eng in hindi_colors.items():
            if hindi in text_lower:
                parsed["color"] = eng
                break
        if "color" not in parsed:
            for color in colors:
                if color in text_lower:
                    parsed["color"] = color
                    break

        # --- Category detection ---
        category_map = {
            "clothing": ["shirt", "kurta", "kurti", "hoodie", "jogger", "jacket",
                         "palazzo", "flannel", "denim", "kapda", "kapde", "clothes",
                         "dress", "top", "pants", "jeans", "tshirt", "t-shirt"],
            "shoes": ["shoe", "sneaker", "loafer", "boot", "jutti", "joota",
                      "chappal", "sandal", "slipper", "footwear", "running shoe",
                      "training shoe"],
            "accessories": ["watch", "belt", "sunglass", "earring", "jhumka",
                           "dupatta", "ghadi", "jewel", "bracelet", "ring"],
            "bags": ["bag", "backpack", "handbag", "tote", "clutch", "purse",
                     "messenger", "duffel", "sling", "wallet"],
        }
        for cat, keywords in category_map.items():
            for kw in keywords:
                if kw in text_lower:
                    parsed["category"] = cat
                    # Also use as search query
                    parsed["query"] = kw
                    break
            if "category" in parsed:
                break

        # --- Brand detection ---
        brands = ["fabindia", "peter england", "biba", "roadster", "wrogn",
                  "levi", "campus", "sparx", "nivia", "hush puppies",
                  "skechers", "woodland", "titan", "fastrack", "casio",
                  "wildcraft", "hidesign", "chumbak", "lavie", "w "]
        for brand in brands:
            if brand in text_lower:
                parsed["brand"] = brand.strip()
                break

        # --- Quantity detection ---
        qty_patterns = [r"(\d+)\s*(?:piece|pcs|qty|quantity|unit|nos)", r"(\d+)\s*(?:of these|items)"]
        for pattern in qty_patterns:
            match = re.search(pattern, text_lower)
            if match:
                parsed["quantity"] = min(int(match.group(1)), 10)
                break

        # If no specific query yet, try to extract product type from text
        if "query" not in parsed:
            # Remove price/action phrases to isolate product terms
            clean = re.sub(r"(?:under|below|above|mujhe|show me|i want|chahiye|dikhao|find me|search for|buy|add to cart|checkout)\s*", "", text_lower)
            clean = re.sub(r"(?:rs\.?|₹|inr)?\s*\d+\s*(?:ke andar|se kam|tak|rupee)?", "", clean)
            clean = clean.strip()
            if clean and len(clean) > 2:
                parsed["query"] = clean

        return parsed

    def _llm_process(self, request: str, result: AgentResult) -> AgentResult:
        """LLM-powered request processing using OpenAI-compatible API."""
        try:
            import openai
            client = openai.OpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL,
            )

            # System prompt with tool descriptions
            system_prompt = """You are an AI shopping assistant for Bharat Bazaar, an Indian fashion marketplace.
You have access to these commerce tools:
1. search_products(query, category, min_price, max_price, color, brand) - Search catalog
2. get_product(product_id) - Get product details
3. check_stock(product_id) - Check availability
4. create_cart() - Create shopping cart
5. add_to_cart(cart_id, product_id, quantity) - Add item to cart
6. create_order(cart_id) - Create order from cart
7. create_checkout(order_id) - Initiate payment

Parse the user's request and respond with a JSON action plan:
{"steps": [{"tool": "tool_name", "params": {...}}, ...], "reasoning": "..."}

If the user wants to search/browse, use search_products.
If the user wants to buy, plan the full flow: search -> get_product -> check_stock -> create_cart -> add_to_cart -> create_order -> create_checkout.
Handle Hindi/Hinglish queries. Extract price, color, category, brand from natural language."""

            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request},
                ],
                temperature=0.3,
            )

            plan_text = response.choices[0].message.content
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                return self._execute_llm_plan(plan, result)
            else:
                # Fallback to rule-based if LLM doesn't return valid JSON
                return self._rule_based_process(request, result)

        except Exception as e:
            # Fallback to rule-based on any LLM error
            result.steps.append(AgentStep(
                0, "llm_parse", f"LLM parsing failed ({str(e)}), falling back to rule-based",
                {"error": str(e)}, status="error"
            ))
            return self._rule_based_process(request, result)

    def _execute_llm_plan(self, plan: dict, result: AgentResult) -> AgentResult:
        """Execute a plan generated by the LLM."""
        steps = plan.get("steps", [])
        step_num = 1
        context = {}  # Store intermediate results

        for step_plan in steps:
            tool_name = step_plan.get("tool", "")
            params = step_plan.get("params", {})

            # Resolve references to previous results
            for key, val in params.items():
                if isinstance(val, str) and val.startswith("$"):
                    resolved = context.get(val.lstrip("$"))
                    if resolved:
                        params[key] = resolved

            step = AgentStep(step_num, tool_name,
                             f"Executing {tool_name}", params)

            # Call the appropriate tool
            tool_method = getattr(self.toolkit, tool_name, None)
            if tool_method:
                step_result = tool_method(**params)
                step.output_data = step_result
                step.status = "success" if step_result.get("success") else "error"

                # Store useful context for subsequent steps
                if step_result.get("success") and step_result.get("data"):
                    data = step_result["data"]
                    if "products" in data and data["products"]:
                        context["product_id"] = data["products"][0]["product_id"]
                    if "cart_id" in data:
                        context["cart_id"] = data["cart_id"]
                    if "order_id" in data:
                        context["order_id"] = data["order_id"]
            else:
                step.status = "error"
                step.output_data = {"error": f"Unknown tool: {tool_name}"}

            result.steps.append(step)
            step_num += 1

            if step.status == "error":
                result.final_summary = f"Failed at step {step_num-1} ({tool_name}): {step.output_data.get('error', 'Unknown error')}"
                return result

        # Build summary from last step
        if result.steps:
            last = result.steps[-1]
            if last.output_data and last.output_data.get("success"):
                result.success = True
                result.final_summary = f"Request completed successfully through {len(result.steps)} tool calls."
            else:
                result.final_summary = "Request completed with issues."

        return result
