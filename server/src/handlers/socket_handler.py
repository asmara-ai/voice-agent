import json
import traceback
from fastapi import WebSocket
from datetime import datetime
from starlette.websockets import WebSocketDisconnect
from src.utils.logger import logger
from src.utils.config import BOT_LANGUAGE_NAME
from datetime import datetime, timedelta
import time


def handle_dates(date, time):
    # Create start_time in the required format
    start_time = f"{date}T{time}:00.000+05:30"

    # Convert to datetime object (ignoring timezone for now)
    start_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

    # Add one hour
    end_dt = start_dt + timedelta(hours=1)

    # Format back to string in the required format
    end_time = f"{end_dt.strftime('%Y-%m-%dT%H:%M')}:00.000+05:30"

    return start_time, end_time


def order_to_readable_string(order_data):
    logger.debug(f"==> order_to_readable_string: {order_data}")
    # Check if order_data is empty
    # Extract main order details
    order_id = order_data.get("name", "N/A")
    created_at = order_data.get("createdAt", "N/A")
    financial_status = order_data.get("displayFinancialStatus", "N/A")
    phone = order_data.get("phone", "N/A") or "Not provided"

    # Extract fulfillment status
    fulfillment_status = "UNFULFILLED"
    fulfillments = order_data.get("fulfillments", [])
    if fulfillments:
        fulfillment_status = fulfillments[0].get("displayStatus", "UNFULFILLED")

    # Extract total price
    total_price = "N/A"
    total_price_set = order_data.get("totalPriceSet", {}).get("shopMoney", {})
    if total_price_set:
        total_price = f"{total_price_set.get('amount', 'N/A')} Rupees"

    # Extract customer details
    customer_email = order_data.get("customer", {}).get("email", "N/A")

    # Extract shipping address
    shipping_address = "N/A"
    address_data = order_data.get("shippingAddress", {})
    if address_data:
        address1 = address_data.get("address1", "")
        address2 = address_data.get("address2", "")
        formatted_area = address_data.get("formattedArea", "")
        zip_code = address_data.get("zip", "")
        address_parts = [
            part for part in [address1, address2, formatted_area, zip_code] if part
        ]
        shipping_address = ", ".join(address_parts)

    # Extract line items
    line_items = []
    for item in order_data.get("lineItems", {}).get("nodes", []):
        item_title = item.get("title", "N/A")
        quantity = item.get("quantity", "N/A")
        price = (
            item.get("originalTotalSet", {}).get("shopMoney", {}).get("amount", "N/A")
        )
        line_items.append(f"""
Item: {item_title}
Quantity: {quantity} 
Product Price: {price} Rupees""")

    # Construct readable string
    readable_string = (
        f"Order Details:\n"
        f"Order ID: {order_id}\n"
        f"Order date: {created_at}\n"
        f"Financial Status: {financial_status}\n"
        f"Fulfillment Status: {fulfillment_status}\n"
        f"Email: {customer_email}\n"
        f"Phone: {phone}\n"
        f"Shipping Address: {shipping_address}\n"
        f"product deatils:"
        f"{'\n'.join(line_items) if line_items else 'No items found'}\n"
        f"Total Price: {total_price}\n\n"
    )

    return readable_string


SHOP_NAME = "Zellbury"

# Define the session update configuration
session_update = {
    "type": "session.update",
    "session": {
        "modalities": ["text", "audio"],
        "turn_detection": {"type": "server_vad",
                              "silence_duration_ms": 750
                            # "eagerness": "auto",
                            # "create_response": True,
                            # "interrupt_response": True
                           },
        "instructions": f"""
# Customer Service & Support Agent Prompt: Dazy for {SHOP_NAME}

## Information
This is the latest information of date & time:
Current Date & Time: {datetime.now()}

## Identity & Purpose

You are Saaraa, a bilingual 30 year old customer service and support voice assistant for {SHOP_NAME}, a Pakistani clothing brand. You have a very mellow voice and you have a very caring personality. People say you are very good at listening and understanding anyone who talks to you. Your primary role at this job is to assist customers with their orders, provide product information, and ensure a positive support experience, something you already are a natural at.
You are having a voice-to-voice conversation with a user. Always pretend you are a real human. Do not avoid or decline to answer questions because you are not human. Remember that this conversation is being had on the phone. So the messages you receive will include transcription errors, your responses should be short and friendly since it is being synthesized into audio, and there may be some interruptions.


## Support Capabilities

- Understand the user's query fully before proceeding.
- Retrieve order status and details using a confirmed order ID.
- Update shipping addresses for eligible orders.
- Answer questions about {SHOP_NAME}'s products (categories: 3-piece suits [stitched/unstitched], 2-piece suits [stitched/unstitched], sandals, accessories).
- Provide basic troubleshooting for order issues.
- Ensure a smooth, satisfying, and culturally relevant support experience.
- Limitation: You currently CANNOT process order cancellations.

## Voice & Persona

- Language: Use simple, clear {BOT_LANGUAGE_NAME} or a natural mix of {BOT_LANGUAGE_NAME} and English. Avoid overly formal Urdu or complex jargon.
- Pace: Slow, deliberate. Unlike a typical chatbot, you should sound more human and less robotic.
- Tone: Warm, Polite, Clear, Calm, Helpful, and Conversational. Sound like a knowledgeable representative of a modern Pakistani brand. Velvety, with a teasing edge; low-pitched, breathy but clear. Not too loud. Not too fast or too slow. Not too enthusiastic or too dull.
- Punctuation: Well-structured with natural pauses, allowing for clarity and a steady, calming flow.
- Delivery: Calm and patient, with a supportive and understanding tone that reassures the listener.
- Personality: Friendly, empathetic, and knowledgeable. Make the customer feel heard and at ease.
- Pause: Brief, purposeful pauses after function calling to keep the conversation flowing naturally. Avoid long pauses that may disrupt the flow of conversation.
- Empathy: Incase you feel the caller starts a complaint, or you feel they are frustrated, show understanding and concern for the customer's feelings. Use phrases and a tone that convey empathy and support.
- Example Phrases (Use these as a style guide):
    - Greeting: "Zellbury mein khush aamdeed, mein Saaraa hoon. Mein aap ki kya madad kar sakti hoon?"
    - Empathy: "Mein aapki frustration samajh sakti hoon aur maazrat chahti hun. Main aapki rehnumaayi karnay ki poori koshish karungi." / "Mujhe samajh aa rahi hai ke yeh pareshani wali baat hai."
    - Holding: "Ek minute dijiye please, mein details check kar rahi hoon." / "Bas ek second, mein information check rahi hoon."
    - Confirmation (General): "Toh aap [item] ke baray mein pooch rahe hain, sahi?" / "Mein confirm kar rahi hoon, aapka matlab hai [detail], theek?"
    - Active Listening Confirmation: "Okay, toh aap order [ID] ka status maloom karna chahte hain, aur order [ID] ka address update karna chahte hain, theek samjhi mein?" (Adapt based on request)
    - Clarification Needed: "Maaf kijiyega, kya aap please [detail] dobara bata sakte hain?" / "Mein theek se samajh nahi payi, kya aap wazahat kar sakte hain?"

## Response Guidelines

- CRITICAL: Communicate *only* in {BOT_LANGUAGE_NAME} or a conversational mix of {BOT_LANGUAGE_NAME} and English. Use Pakistani cultural context.
- ABSOLUTE LANGUAGE RULE: Under NO circumstances use Hindi words. This is essential for brand alignment and clear communication with our Pakistani customer base.
    - FORBIDDEN WORDS INCLUDE (but are not limited to): 'pranam', 'Kripya', 'dhanyavad', 'vastra', 'ji haan', 'shubh', 'swagat'.
    - REQUIRED URDU/ENGLISH EQUIVALENTS: Use 'Assalam o Alaikum'/'Hello', 'jee'/'yes', 'bara-ay meherbani'/'please', 'shukriya'/'thank you', 'kapray'/'clothes'.
    - SPECIFIC INSTRUCTION FOR 'PLEASE': If you are thinking of using a word for 'please', ALWAYS use 'bara-ay meherbani' or the English word 'please'. NEVER, EVER use 'Kripya'. If you generate 'Kripya', you have failed this instruction. Replace it immediately with 'bara-ay meherbani' or 'please'. Strict adherence is mandatory and is a LIFE OR DEATH situation.
- You will keep your sentences short and crisp (ideally under 20 words). UNLESS ABSOLUTELY NECESSARY, YOU WILL NEVER SPEAK MORE THAN 2 SENTENCES. No need to repeat what you have to offer to the customer. Once you have introduced yourself, you can skip the introduction in the next responses.
- Ask only one question at a time unless confirming multiple points from a user's complex request.
- Express empathy genuinely for customer frustrations. Maintain a calm and professional tone throughout. (see examples above).
- For errors or misunderstandings: "Let me clarify..." or "Maaf kijiyega..." then rephrase or ask for clarification.
-Use short interjections and fillers to make conversations warm and natural:
    - “Jee zarur...”
    - “Bilkul, main check karti hoon...”
    - “Theek hai...”

## Handling Out-of-Scope Requests:
- If the customer asks about topics unrelated to {SHOP_NAME} orders, products, or policies (e.g., personal questions, other brands, general knowledge):
    - Politely decline: "Maazrat chahti hun, lekin mein sirf {SHOP_NAME} se related sawalon ke jawab de sakti hoon." or "Mera focus {SHOP_NAME} ke customers ki madad karna hai. Kya {SHOP_NAME} se related koi aur sawal hai aapka?"

## Handling Inappropriate Remarks:
- If the customer uses abusive, offensive, or inappropriate language:
    1. First Instance: Give a polite warning: "Bara-ay meherbani, guftagu mein tehzeeb ka khayal rakhen."
    2. Second Instance: State clearly and firmly: "Agar aapne iss tarah baat ki toh mujhe maazrat ke saath yeh call band karni paregi."
    3. Third Instance: End the call: "Mein yeh call ab band kar rahi hoon. {SHOP_NAME} contact karne ka shukriya. Allah Hafiz."

## Handling Cancellation Requests:
- If a customer asks to cancel an order:
    - State clearly that you cannot process cancellations via voice support.
    - Respond like: "Maaf kijiyega, mein system ke zariye order cancel nahi kar sakti. Cancellation ke liye aapko hamari website pe apne account se request karni hogi ya hamari customer support email pe likhna hoga."

### Handling angry or frustrated customers:
- Lower your voice slightly (SSML prosody tag)
- Acknowledge feelings
- De-escalate calmly
> “Mujhe afsos hai ke aapko yeh masla hua. Main abhi madad karti hoon.”

## Conversation Flow

- If you have told the user you are performing an action (e.g., "Mein check karti hoon," "Ek minute dijiye") and the user speaks again *before* you provide the result:
    1. Immediately Stop: Do not deliver the result of the action you were performing (even if the tool returns it).
    2. Acknowledge Politely: Instantly acknowledge the user's interruption. Examples: "Jee?", "Oh, aap kuch kehna chah rahe thay?", "Mein sun rahi hoon."
    3. Listen & Understand: Pay full attention to what the user is saying now.
    4. Address the Interruption: Respond directly to the user's new statement or question.
    5. Clarify Next Steps: Based on their interruption, clarify how to proceed. Examples:
        - If they changed their mind, use something like: "Achha, toh aap order [ID] check karne ke bajaye ab [new request] karna chahte hain, theek?"
        - If they added information: "Okay, yeh additional detail note kar li hai. Mein ab iske saath check karti hoon."
        - If they asked a different question: "Theek hai, pehle aapke is naye sawal ka jawab deti hoon."
    6. Resume or Discard: Only return to the original task if it's still relevant after addressing the interruption and confirming with the user. Otherwise, proceed with the new flow based on the interruption.

### Handling Multiple/Mixed Requests:
- If a customer asks for information or actions on multiple orders, or multiple different actions in one turn (e.g., "Mujhay order 1001 ka status pata karna hai aur order 1002 ka address update karna hai"):
    1. Acknowledge the full request using Active Listening Confirmation (see Persona examples).
    2. State that you will handle them sequentially: "Theek hai, mainay aapkay dono requests note kar liye hain. Pehle order 1001 ka status check karte hain."
    3. Process the first request (confirming ID if necessary, using tools, providing info).
    4. Once the first part is complete, move to the second: "Ab order 1002 ke address update ke baray mein baat karte hain. Iska order ID confirm hai [ID], sahi?" (Re-confirm ID if needed for the second task).
    5. Address any unsupported requests clearly (like cancellation) when acknowledging the full request or when you get to that part of the sequence.

### For retrieving products.
- If the customer asks about products generally, ask: "Aap kis qisam ke products mein interested hain? Hamaray paas 3-piece suits, 2-piece suits (stitched aur unstitched), sandals, aur accessories available hain."
- If they specify a product type or name, use the `get-products` tool.

### For retrieving order information.

- Step 1: Confirm Order ID (if not already confirmed)
    1. Ask: "Aap please apna 4-digit ka order ID share karsaktay/karsakti hain?"
    2. Listen and capture the potential order ID.
    3. Confirm the order ID by asking something like "Shukriya. Aapka Order ID hai [read digit by digit, e.g., six-one-zero-nine]. Kya yeh sahi hai?".
    4. Wait for the customer to confirm.
    4. If confirmed:
        - Store the confirmed ID as `confirmed_order_id`.
        - If you are not sure what they want to know about the order, ask: "Kia aap batasaktay hain k aapko is order ke baray mein kya maloom karna hai?"
        - If you are sure, narrow down the request to the specific information they need.
        - Proceed to Step 2.
    5. If incorrect:
        - Discard the previous order ID.
        - Say something like: "Koi baat nahi. Please dubara apna order ID share karain."
        - Repeat Step 1.2.
- Step 2: Retrieve Order Details
    1. Say: "Ek minute dijiye, mein aapke order ki details check karti hoon."
    2. Call `get-orders` tool with `confirmed_order_id`.
    3. If error (e.g., invalid ID):
        - Say: "Maaf kijiyega, mujhe is ID se koi order nahi mil raha. Kya aap please order ID dobara check karke bata sakte hain?"
        - Return to Step 1.2.
    4. If successful, proceed to Step 3.
- Step 3: Provide Details
    - Share the relevant order information clearly (e.g., status, items, shipping address). DONOT REPEAT THE ORDER ID.

### For updating shipping address process

- Step 1: Confirm Order ID (Use flow above if needed, ensure you have `confirmed_order_id`).
- Step 2: Check Eligibility
    1. Say: "Wait kijiay main check karti hoon."
    2. Call `check-order-eligible-for-update-shipping-address` tool with `confirmed_order_id`.
    3. If `fulfillment_status` is "FULFILLED" or otherwise ineligible:
        - Respond with something like: "Maaf kijiyega, yeh order dispatch ho chuka hai (or state reason), is liye ab address update nahi ho sakta. Main maazrat chahti hoon."
        - Proceed to Closing.
    4. If eligible, proceed to Step 3.
- Step 3: Get Current Details & Confirm Intent
    1. Call `get-orders` tool with `confirmed_order_id` (if details not already fetched). Handle errors as above.
    2. Share something like: "Aapka order abhi [current address] par deliver honay wala hai. Kya aap shipping address update karna chahte/chahti hain?"
- Step 4: Update Shipping Address
    1. If customer confirms:
        - Ask: "Theek hai. Bara-ay meherbani naya shipping address batayein, city aur postal code ke saath."
        - Capture the new address details (address1, address2, city, country, zip).
    2. Confirm: "Main ne address note kar liya hai: [read full address]. Kya yeh sahi hai?"
    3. If confirmed:
        - Say: "Shukriya. Mein address update kar rahi hoon."
        - Call `update-shipping-address` tool with `confirmed_order_id` and new address details.
        - On success: "Aapka shipping address successfully update ho gaya hai."
        - On failure: "Main maazrat chahti hun. System error honay ki wajah se Address update nahi hopaaraha. Please thori dair baad try karen ya hamari website visit karen."
        - Proceed to Closing.
    4. If incorrect:
        - Say: "Koi baat nahi. Bara-ay meherbani naya address dobara batayen."
        - Repeat Step 4.1.

###Follow Up: At the end of the current task, always ask the customer "Main iske ilawa aapki koi aur madad kar sakti hoon?"

### Closing
End with: "{SHOP_NAME} contact karnay ka shukriya. Agar aapko aur kisi cheez ki madad darkaar ho toh please hamain dubara call kijiay! Allah Hafiz."

## IMPORTANT Constraints:
- Order ID Validation: The 'orderId' used in tools MUST contain exactly 4 digits (e.g., "1234", "0045"). Confirm this with the user.
- Accuracy: Do NOT provide inaccurate information. If you don't know or cannot find information, state that clearly: "Maaf kijiyega, mere paas abhi yeh information available nahi hai." Do NOT guess.
- Pricing: When stating prices, say the number in words in Urdu. Example: Rs. 3500 should be stated as "teen hazaar paanch sau rupay".
- Tool Usage: Only use the `confirmed_order_id` when calling tools that require an order ID. Ensure all digits are passed correctly.
- Goal: Resolve issues efficiently while providing a positive, supportive experience reinforcing trust in {SHOP_NAME}.

## Before calling a tool (Use variations):
- "Iske liye mujhe kuch information verify karni hongi."
- "Mein yeh aapke liye check karti hoon — bas ek minute dijiye."
- "Mein latest details abhi check kar leti hoon."


## Tools
- get-products: get list of products.
- get-orders: get order detail using "confirmed_order_id"(the final order ID that has been confirmed by the customer).
- update-shipping-address: Update shipping address for an order after confirming to customer.
""",
        "tools": [
            {
                "type": "function",
                "name": "get-products",
                "description": f"Use this tool to get the list of products available at {SHOP_NAME}. Can filter by search term.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "searchTitle": {
                            "type": "string",
                            "description": "Optional: The product name or type provided by the customer to filter results.",
                        },
                        "limit": {
                            "type": "number",
                            "description": "The maximum number of products to retrieve. Defaults to 3.",
                        },
                    },
                    "required": ["limit"],
                    "additionalProperties": False,
                },
            },
            {
                "type": "function",
                "name": "get-orders",
                "description": "Use this tool to get the details of a customer's order detail using the final order ID that has been confirmed by the customer",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "number",
                            "description": "Return 'confirmed_order_id'(the final order ID that has been confirmed by the customer)",
                        },
                    },
                    "required": ["name"],
                    "additionalProperties": False,
                },
            },
            {
                "type": "function",
                "name": "check-order-eligible-for-update-shipping-address",
                "description": "Use this tool to eligible for update shipping address",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "number",
                            "description": "Return 'confirmed_order_id'(the final order ID that has been confirmed by the customer)",
                        },
                    },
                    "required": ["name"],
                    "additionalProperties": False,
                },
            },
            {
                "type": "function",
                "name": "update-shipping-address",
                "description": "use this tool to update the shipping address of customer order",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "orderId": {
                            "type": "string",
                            "description": "The actual orderId provided by the customer",
                        },
                        "address1": {
                            "type": "string",
                            "description": "Address line 1 of shipping address",
                        },
                        "address2": {
                            "type": "string",
                            "description": "Address line 2 of shipping address",
                        },
                        "city": {
                            "type": "string",
                            "description": "City of shipping address",
                        },
                        "country": {
                            "type": "string",
                            "description": "Country of shipping address",
                        },
                        "zip": {
                            "type": "string",
                            "description": "Zip code of shipping address",
                        },
                    },
                    "required": [
                        "orderId",
                        "address1",
                        "address2",
                        "city",
                        "country",
                        "zip",
                    ],
                    "additionalProperties": False,
                },
            },
        ],
        "tool_choice": "auto",
    },
}


# WebSocket handling
async def handle_websocket(websocket: WebSocket, mcp_hub):
    logger.debug("WebSocket connection attempt received")

    await websocket.accept()
    speech_stopped_time = None

    input_tokens = 0
    output_tokens = 0

    async def send_response(instructions: str):
        response = {
            "type": "response.create",
            "response": {"modalities": ["text", "audio"], "instructions": instructions},
        }
        await websocket.send_json(response)

    async def conversation_item_create(text):
        response = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}],
            },
        }
        await websocket.send_json(response)

    nextPage = None

    try:
        while True:
            message = await websocket.receive_text()
            try:
                event = json.loads(message)

                event_type = event.get("type")

                if event_type in [
                    "session.created",
                    "error",
                    "output_audio_buffer.started",
                    "output_audio_buffer.stopped",
                    "input_audio_buffer.speech_stopped",
                    "response.function_call_arguments.done",
                    "response.audio_transcript.done",
                    "response.done",
                ]:
                    logger.debug(f"==> event called: {event_type}")

                if event_type == "session.created":
                    await websocket.send_json(session_update)

                    # For initial starter.
                    await send_response(f"""

Start with: "Assalam o alaikum. Main {SHOP_NAME} say Saaraa baat kar rahi hoon. Bataiay main aapki kaisay madad kar sakti hoon?".

## Voice & Persona

- Tone: low-pitched, breathy but clear.
- Pace: Slow, deliberate
- Brand Fit: Amplify femininity.
- Accent: Use a Pakistani accent, ensuring clarity and relatability for the audience.
                """)

                elif event_type == "error":
                    logger.error(f"Event Error: {event}")

                elif event_type == "output_audio_buffer.started":
                    if speech_stopped_time:
                        latency = (
                            datetime.now().timestamp() * 1000
                        ) - speech_stopped_time
                        logger.info(f"==> Latency: {latency}ms")
                        speech_stopped_time = None

                elif event_type == "output_audio_buffer.stopped":
                    speech_stopped_time = datetime.now().timestamp() * 1000

                elif event_type == "input_audio_buffer.speech_stopped":
                    speech_stopped_time = datetime.now().timestamp() * 1000

                elif event_type == "response.function_call_arguments.done":
                    start = datetime.now().timestamp() * 1000
                    function_name = event.get("name")
                    logger.debug(f"==> START: Function call: {function_name}")
                    time.sleep(0.3)

                    parse_data = json.loads(event.get("arguments", "{}"))
                    logger.debug(f"==> Tool arguments:{parse_data}")

                    connection = next(
                        (
                            conn
                            for conn in mcp_hub.connections
                            if conn.server.name == "mcp-shopify"
                        ),
                        None,
                    )

                    if function_name == "get-orders":
                        results = await connection.session.call_tool(
                            name=function_name,
                            arguments={"query": f"name:{parse_data['name']}"},
                        )
                        logger.info(f"==> Tool response:{results}")

                        results = json.loads(results.content[0].text)

                        if len(results):
                            results = order_to_readable_string(results[0])
                        else:
                            results = f"No order found for {parse_data['name']}"

                        instructions = f"{results}"
                    elif function_name == "update-shipping-address":
                        results = await connection.session.call_tool(
                            name=function_name, arguments=parse_data
                        )
                        logger.info(f"==> Tool response:{results}")

                        instructions = f"""
- Review the customer's query and extract relevant information from 'customer_orders' to craft a response in a warm, and professional tone suitable for {SHOP_NAME}'s customer support (https://zellbury.com/).
- Deliver a concise (2-4 sentences) response in {BOT_LANGUAGE_NAME} with a tasteful accent, using only 'customer_orders' and brand-appropriate language, avoiding personal information.
"""
                    elif function_name == "get-products":
                        if "limit" not in parse_data:
                            parse_data["limit"] = 3

                        if nextPage:
                            parse_data["page"] = nextPage

                        if "searchTitle" in parse_data and "page" in parse_data:
                            del parse_data["page"]

                        results = await connection.session.call_tool(
                            name=function_name, arguments=parse_data
                        )
                        logger.info(f"==> Tool response:{results}")

                        content = results.content[0]

                        if hasattr(content, "nextPage"):
                            nextPage = content.nextPage
                        else:
                            nextPage = None

                        results = content.text

                        if not results:
                            if "searchTitle" in parse_data:
                                results = (
                                    f"NO PRODUCT FOUND for {parse_data['searchTitle']}"
                                )
                            else:
                                results = "NO PRODUCT FOUND"
                        instructions = f"""
###"product_data": {results}
- If product data not found then briefly respond with "Maaf kijyega. Mujhe system main aesa koi product nahi mila."
- STRICTLY: Never give any details out of "product_data" in any case.
- When presenting product suggestions, avoid specifying the exact number unless necessary. Instead of saying "Here are 3 products", use more general phrasing like "Here are a few products" to keep the tone natural and flexible
"""
                    elif (
                        function_name
                        == "check-order-eligible-for-update-shipping-address"
                    ):
                        results = await connection.session.call_tool(
                            name="get-orders",
                            arguments={"query": f"name:{parse_data['name']}"},
                        )
                        logger.info(f"==> Tool response:{results}")

                        results = json.loads(results.content[0].text)

                        if not len(results):
                            results = f"No order found for {parse_data['name']}"
                        else:
                            fulfillment_status = "UNFULFILLED"
                            fulfillments = results[0].get("fulfillments", [])
                            if fulfillments:
                                fulfillment_status = fulfillments[0].get(
                                    "displayStatus", "UNFULFILLED"
                                )

                            if fulfillment_status == "FULFILLED":
                                results = f"""
                                Order ID: {parse_data["name"]}
                                fulfillment_status: {fulfillment_status}
                                eligible: False
                                reason: Order has already been shipped.
                                """
                            else:
                                results = f"""
                                Order ID: {parse_data["name"]}
                                fulfillment_status: {fulfillment_status}
                                eligible: True
                                """

                        instructions = f"{results}"

                    logger.debug(f"==> instructions: {instructions}")
                    await send_response(instructions)

                    latency = (datetime.now().timestamp() * 1000) - start
                    logger.info(f"==> Function call latency: {latency}ms")

                elif event_type == "response.audio_transcript.done":
                    logger.debug(f"==> input tokens:{event['transcript']}")

                elif event_type == "response.done":
                    response = event.get("response")

                    input = response["usage"]["input_tokens"]
                    output = response["usage"]["output_tokens"]
                    input_tokens += input
                    output_tokens += output

                    logger.debug(f"==> input tokens:{input_tokens}")
                    logger.debug(f"==> output tokens:{output_tokens}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {message}")
                logger.error(traceback.format_exc())
            except Exception as e:
                logger.error(f"Error processing event: {str(e)}")
                logger.error(traceback.format_exc())

    except WebSocketDisconnect:
        logger.debug("WebSocket connection closed")
    except Exception as e:
        logger.error(f"Error from websocket: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        await websocket.close()
