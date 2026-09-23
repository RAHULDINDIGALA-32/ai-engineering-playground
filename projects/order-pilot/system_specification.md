# Order-Pilot

## Restaurant Order Management AI Agent System — LangGraph

---

# 1. SYSTEM OBJECTIVE

Build a production-oriented restaurant order-management AI agent system named **Order-Pilot** using **LangGraph**.

Order-Pilot accepts natural-language food orders from a user, extracts structured order information, validates the order against a restaurant menu/inventory, handles partial availability and user decisions, coordinates cooking and serving through deterministic workflow nodes, manages bounded retries, and produces a final order result.

The system must be:

* Modular
* Deterministic where business logic is involved
* LLM-assisted only where language understanding/generation is required
* Explicitly state-driven
* Testable
* Reproducible
* Resistant to invalid state transitions
* Easy to extend with real restaurant integrations later

---

# 2. CORE ARCHITECTURAL PRINCIPLE

## 2.1 LLM Responsibilities

The LLM is responsible for:

1. Understanding natural-language user input.
2. Determining whether the input is related to restaurant food ordering.
3. Extracting requested dishes and quantities.
4. Understanding the user's response to a partial-order proposal.
5. Generating natural-language responses to the user.

The LLM MUST NOT be responsible for:

* Checking menu inventory directly.
* Deciding whether an order is available.
* Incrementing/decrementing retry counters.
* Deciding whether a retry is allowed.
* Simulating cooking.
* Simulating serving.
* Directly modifying workflow status.
* Choosing LangGraph edges.
* Bypassing retry limits.
* Determining terminal workflow states.

These responsibilities belong to deterministic application nodes and LangGraph routing functions.

---

# 3. HIGH-LEVEL ARCHITECTURE

The workflow should conceptually follow:

```text
                    ┌──────────────────┐
                    │      START       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  User Input /    │
                    │  LLM Extraction  │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ Input Validation │
                    └────────┬─────────┘
                             │
                   ┌─────────▼──────────┐
                   │ Order Confirmation │
                   │ Menu / Inventory   │
                   └─────────┬──────────┘
                             │
                 ┌───────────┼────────────┐
                 │           │            │
                 ▼           ▼            ▼
             CONFIRMED    PARTIAL        NA
                 │           │            │
                 │           └────┬───────┘
                 │                │
                 │                ▼
                 │       User Decision / LLM
                 │                │
                 │        ┌───────┴────────┐
                 │        │                │
                 │        ▼                ▼
                 │    ACCEPT PARTIAL    NEW ORDER
                 │        │                │
                 │        │                ▼
                 │        │       New Order Input
                 │        │                │
                 │        │         Order Retry Check
                 │        │                │
                 │        └────────┬───────┘
                 │                 │
                 └─────────────────┘
                             │
                             ▼
                          COOK
                             │
                       ┌─────┴─────┐
                       │           │
                       ▼           ▼
                 COOK_COMPLETED  COOK_FAILED
                       │           │
                       │      retry remaining?
                       │        │       │
                       │       yes      no
                       │        │       │
                       │        └──►COOK │
                       │                │
                       │                ▼
                       │               END
                       ▼
                      SERVE
                       │
                 ┌─────┴─────────┐
                 │               │
                 ▼               ▼
           SERVE_COMPLETED   SERVE_FAILED
                 │               │
                 │       cook retry remaining?
                 │          │           │
                 │         yes          no
                 │          │           │
                 │          ▼           ▼
                 │        COOK       SERVE
                 │          │           │
                 │          └─────┬─────┘
                 │                │
                 ▼                ▼
          ORDER_COMPLETED        END
```

The exact implementation may use additional helper/router nodes, but the business semantics above MUST remain unchanged.

---

# 4. MODULAR PROJECT STRUCTURE

Use a modular file structure.

Recommended structure:

```text
order-pilot/
│
├── src/
│   ├── graph/
│   │   ├── graph.py
│   │   ├── edges.py
│   │   └── routers.py
│   │
│   ├── state/
│   │   └── state.py
│   │
│   ├── nodes/
│   │   ├── order_parser.py
│   │   ├── order_confirmation.py
│   │   ├── user_decision.py
│   │   ├── cook.py
│   │   ├── serve.py
│   │   └── response.py
│   │
│   ├── services/
│   │   ├── menu_service.py
│   │   ├── inventory_service.py
│   │   └── llm_service.py
│   │
│   ├── models/
│   │   ├── order.py
│   │   └── enums.py
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   └── main.py
│
├── tests/
│   ├── unit/
│   │   ├── test_order_parser.py
│   │   ├── test_order_confirmation.py
│   │   ├── test_cook.py
│   │   ├── test_serve.py
│   │   └── test_routers.py
│   │
│   ├── integration/
│   │   └── test_order_workflow.py
│   │
│   └── scenarios/
│       ├── test_tc01.py
│       ├── test_tc02.py
│       └── test_tc03.py
│
├── prompt.md
├── README.md
├── requirements.txt
└── .env.example
```

Do NOT put the entire workflow into a single Python file.

---

# 5. DOMAIN MODEL

Use explicit domain models/enums instead of scattered strings.

## 5.1 Order Status

```text
ORDER_RECEIVED
ORDER_CONFIRMED
ORDER_PARTIAL
ORDER_NA
ORDER_COOKING
ORDER_READY
ORDER_SERVING
ORDER_COMPLETED
ORDER_FAILED
ORDER_CANCELLED
```

Only statuses that are actually required by the implementation should be used, but state transitions must be explicit.

---

# 6. ORDER ITEM REPRESENTATION

Do NOT represent the order internally only using parallel arrays such as:

```python
dishes: list[str]
required_quantities: list[int]
available_quantities: list[int]
```

Parallel arrays can become inconsistent.

Instead, use:

```python
OrderItem:
    dish_name: str
    requested_quantity: int
    available_quantity: int
    accepted_quantity: int
```

Example:

```python
[
    {
        "dish_name": "Pizza",
        "requested_quantity": 3,
        "available_quantity": 2,
        "accepted_quantity": 0
    },
    {
        "dish_name": "Burger",
        "requested_quantity": 1,
        "available_quantity": 1,
        "accepted_quantity": 0
    }
]
```

If compatibility with the original specification is required, derived arrays may be exposed, but they MUST NOT be the source of truth.

The `OrderItem` list is the canonical representation.

---

# 7. LANGGRAPH SHARED STATE

Define one strongly typed shared state.

Recommended conceptual structure:

```python
class OrderState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    order_items: list[OrderItem]

    status: OrderStatus

    order_attempts_remaining: int
    cook_attempts_remaining: int
    serve_attempts_remaining: int

    partial_order_decision: str | None

    final_result: str | None

    error_message: str | None
```

The exact implementation may use `TypedDict`, Pydantic models, or another strongly typed representation, but the semantics MUST remain equivalent.

---

# 8. MESSAGE STATE

The graph must maintain conversational history using LangGraph message state.

Use:

```python
messages: Annotated[list[BaseMessage], add_messages]
```

The message history should contain:

* User input
* Assistant responses
* Relevant system/tool information where appropriate

Do not use message history as the authoritative source for business state.

Business state must be stored explicitly in structured state fields.

---

# 9. RETRY COUNTERS

Initialize:

```text
order_attempts_remaining = 3
cook_attempts_remaining = 2
serve_attempts_remaining = 2
```

Important:

## Order attempts

An order attempt means a user-submitted/revised order.

The initial order consumes one order attempt.

Therefore:

```text
Initial order -> 1st attempt
New order     -> 2nd attempt
New order     -> 3rd attempt
```

After the third order attempt, no further order submission is allowed.

The system must terminate with:

```text
ORDER_FAILED
```

if the user still has not produced an acceptable order.

Do not allow an unlimited loop between the user and order parser.

---

# 10. COOK RETRIES

Cook has a maximum of **2 total execution attempts**.

Example:

```text
cook attempt #1 -> failed
cook attempt #2 -> success
```

After the second cook attempt:

```text
cook_attempts_remaining == 0
```

The cook node MUST NOT be called again.

---

# 11. SERVE RETRIES

Serve has a maximum of **2 total execution attempts**.

Example:

```text
serve attempt #1 -> failed
serve attempt #2 -> success
```

After the second failed serve attempt:

```text
serve_attempts_remaining == 0
```

The order must terminate with:

```text
ORDER_FAILED
```

---

# 12. CRITICAL RETRY RULE

If serving fails:

### Case A — Cook retries remain

If:

```text
serve_attempts_remaining > 0
AND
cook_attempts_remaining > 0
```

then:

```text
SERVE_FAILED
    ↓
COOK
    ↓
SERVE
```

The reason is that a failed serving operation may require the order to be prepared again before another serving attempt.

### Case B — Cook retries exhausted

If:

```text
serve_attempts_remaining > 0
AND
cook_attempts_remaining == 0
```

then do NOT call cook again.

Instead:

```text
SERVE_FAILED
    ↓
SERVE
```

This allows the remaining serve attempt to be used without violating the cook retry limit.

### Case C — Serve retries exhausted

If:

```text
serve_attempts_remaining == 0
```

terminate:

```text
ORDER_FAILED
```

This rule is required to make TC03 internally consistent.

---

# 13. MENU / INVENTORY

Create a deterministic menu/inventory service.

Example:

```python
MENU = {
    "pizza": 5,
    "burger": 2,
    "pasta": 0,
    "biryani": 10,
}
```

The menu service must expose deterministic availability.

Example:

```python
get_available_quantity("pizza")
```

returns:

```text
5
```

If a dish does not exist:

```text
0
```

The LLM must NOT directly inspect the menu.

---

# 14. ORDER PARSER NODE

Node:

```text
order_parser
```

Responsibilities:

1. Read the latest user message.
2. Determine whether the request is food-ordering related.
3. Extract dish names.
4. Extract quantities.
5. Normalize obvious language variations.

Example:

```text
"I want two burgers and 1 pizza"
```

becomes:

```json
{
  "order_items": [
    {
      "dish_name": "burger",
      "requested_quantity": 2
    },
    {
      "dish_name": "pizza",
      "requested_quantity": 1
    }
  ]
}
```

The parser MUST NOT check availability.

---

# 15. UNRELATED INPUT

If the user asks something unrelated to food ordering:

Example:

```text
"What is the capital of France?"
```

the system should respond that Order-Pilot is a restaurant food-ordering assistant.

The system should then wait for a valid food order.

An unrelated request MUST NOT:

* Consume a cook attempt.
* Consume a serve attempt.
* Change menu availability.
* Trigger cooking.
* Trigger serving.

Whether an unrelated input consumes an order attempt should be explicitly defined as:

```text
NO
```

Only valid order submissions consume an order attempt.

---

# 16. INVALID ORDER INPUT

Handle cases such as:

```text
"I want something"
"I want food"
"Give me some pizza"
```

where quantity is missing or ambiguous.

The system should ask the user for the missing quantity rather than silently assuming one.

Do not mutate inventory or retry counters for an incomplete order.

---

# 17. ORDER CONFIRMATION NODE

Node:

```text
order_confirmation
```

This node is deterministic.

Responsibilities:

1. Read `order_items`.
2. Query the menu/inventory service.
3. Populate `available_quantity`.
4. Determine overall order availability.
5. Update `status`.

For each item:

```text
available_quantity = menu[dish_name]
```

If the dish does not exist:

```text
available_quantity = 0
```

---

# 18. ORDER AVAILABILITY RULES

## Case 1 — Fully available

For every item:

```text
available_quantity >= requested_quantity
```

Set:

```text
status = ORDER_CONFIRMED
```

Set:

```text
accepted_quantity = requested_quantity
```

Proceed to:

```text
COOK
```

---

## Case 2 — Partially available

At least one item has:

```text
0 < available_quantity < requested_quantity
```

or some requested items are available while others are unavailable.

Set:

```text
status = ORDER_PARTIAL
```

The user must decide whether to accept the available portion or submit a new order.

---

## Case 3 — Completely unavailable

If every requested item has:

```text
available_quantity == 0
```

set:

```text
status = ORDER_NA
```

The user must submit a new order.

---

# 19. ACCEPTING A PARTIAL ORDER

If the user accepts the partial order:

```text
accepted_quantity = min(
    requested_quantity,
    available_quantity
)
```

Items with:

```text
accepted_quantity == 0
```

must not be sent to cooking.

The resulting accepted order becomes the order passed to the cook node.

---

# 20. REJECTING A PARTIAL ORDER

If the user rejects the partial order:

```text
partial_order_decision = "NEW_ORDER"
```

request another order from the user.

The new valid order consumes one order attempt.

Do not reset:

```text
order_attempts_remaining
cook_attempts_remaining
serve_attempts_remaining
```

during a new-order cycle.

Only the order data itself is replaced.

---

# 21. USER DECISION NODE

The user-decision handling may use an LLM because natural-language interpretation is required.

Examples:

```text
"Yes, I'll take what you have."
```

→

```text
ACCEPT_PARTIAL
```

Example:

```text
"No, give me something else."
```

→

```text
NEW_ORDER
```

Ambiguous responses must result in a clarification request.

Do not guess.

---

# 22. ROUTING MUST BE DETERMINISTIC

Create explicit routing functions.

For example:

```python
route_after_confirmation(state)
route_after_cook(state)
route_after_serve(state)
route_after_user_decision(state)
```

The router must inspect structured state.

Do NOT ask the LLM:

```text
"Should we call cook?"
```

Instead:

```python
if state["status"] == ORDER_CONFIRMED:
    return "cook"
```

Likewise, retry decisions must be implemented as deterministic code.

---

# 23. COOK NODE

Node:

```text
cook
```

Responsibilities:

1. Verify a cook attempt is available.
2. Consume one cook attempt.
3. Simulate cooking.
4. Produce either success or failure.

For testing, use a controllable probability/configuration.

Default simulation:

```text
33% failure
67% success
```

However, tests MUST be able to inject deterministic outcomes.

Do not rely on random behavior for automated tests.

For example:

```python
CookSimulator([
    "FAIL",
    "SUCCESS"
])
```

This allows TC02 and TC03 to be reproduced exactly.

---

# 24. COOK SUCCESS

If cooking succeeds:

```text
status = ORDER_READY
```

Route:

```text
COOK → SERVE
```

---

# 25. COOK FAILURE

If cooking fails:

```text
status = ORDER_FAILED
```

temporarily record the failure reason.

Then:

```text
if cook_attempts_remaining > 0:
    retry COOK
else:
    terminate
```

If no attempts remain:

```text
status = ORDER_FAILED
```

and generate an appropriate user-facing apology.

---

# 26. SERVE NODE

Node:

```text
serve
```

Responsibilities:

1. Verify serve attempts remain.
2. Consume one serve attempt.
3. Simulate serving.
4. Produce success/failure.

Again, tests must be able to inject deterministic outcomes.

Example:

```python
ServeSimulator([
    "FAIL",
    "SUCCESS"
])
```

---

# 27. SERVE SUCCESS

If serving succeeds:

```text
status = ORDER_COMPLETED
final_result = "SUCCESS"
```

Generate a concise user-facing completion message.

Then:

```text
END
```

---

# 28. SERVE FAILURE

If serving fails:

```text
status = ORDER_FAILED
```

temporarily record the failure reason.

Then apply the retry rules defined in Section 12.

The router MUST NOT exceed:

```text
serve_attempts_remaining <= 2
cook_attempts_remaining <= 2
```

---

# 29. TERMINAL STATES

The graph must terminate in one of the following states:

```text
ORDER_COMPLETED
ORDER_FAILED
ORDER_CANCELLED
```

For this initial implementation, `ORDER_CANCELLED` may remain unused unless explicitly required.

Every terminal path must produce:

```text
final_result
```

---

# 30. FINAL RESULT

The final state must explicitly indicate whether the order completed.

Example:

```python
final_result = {
    "success": True,
    "status": "ORDER_COMPLETED"
}
```

or:

```python
final_result = {
    "success": False,
    "status": "ORDER_FAILED"
}
```

Do not infer final success merely from the last message.

---

# 31. USER-FACING RESPONSES

User-facing responses should be generated through a response layer/LLM.

Examples:

### Unrelated input

```text
I'm Order-Pilot, a restaurant ordering assistant. I can help you place food orders, but I can't assist with general questions.
```

### Partial order

```text
We currently have 2 burgers available, but you requested 4. Would you like to proceed with the 2 available burgers, or would you like to place a different order?
```

### Cook failure

```text
I'm sorry, we couldn't prepare your order successfully. We'll try preparing it once more.
```

### Final failure

```text
I'm sorry, but we weren't able to complete your order after the available attempts. Please try again later.
```

### Success

```text
Your order has been prepared and served successfully. Thank you!
```

The exact wording may vary, but responses must remain polite, concise, and contextually correct.

---

# 32. STATE MUTATION RULES

Nodes must follow single-responsibility principles.

## order_parser

May modify:

```text
messages
order_items
```

## order_confirmation

May modify:

```text
order_items.available_quantity
order_items.accepted_quantity
status
```

## user_decision

May modify:

```text
partial_order_decision
messages
```

## cook

May modify:

```text
cook_attempts_remaining
status
error_message
```

## serve

May modify:

```text
serve_attempts_remaining
status
error_message
```

## response layer

May modify:

```text
messages
final_result
```

Do not allow arbitrary nodes to mutate unrelated fields.

---

# 33. INVENTORY MUTATION

For this initial implementation, menu availability may be static.

However, architect the inventory layer so it can later be replaced with:

```text
Database
REST API
Restaurant POS
Redis
Inventory service
```

Do not hard-code inventory access throughout graph nodes.

Use:

```text
order_confirmation → inventory_service → menu source
```

---

# 34. IMPORTANT IDEMPOTENCY REQUIREMENT

The workflow should avoid accidentally consuming multiple retry attempts because of repeated execution of the same node.

Each actual node execution should correspond to exactly one business attempt.

State transitions must be explicit.

---

# 35. GRAPH DESIGN REQUIREMENTS

The graph must use:

* Explicit nodes
* Explicit conditional edges
* Typed shared state
* Deterministic routers
* Bounded retry loops
* Clear terminal edges

Avoid hidden control flow inside LLM prompts.

The LLM must never be able to output:

```text
"CALL_COOK"
```

and thereby directly control graph execution.

Instead, structured LLM output should only represent semantic information such as:

```json
{
    "intent": "food_order",
    "order_items": [...]
}
```

or:

```json
{
    "decision": "ACCEPT_PARTIAL"
}
```

LangGraph decides what happens next.

---

# 36. STRUCTURED LLM OUTPUT

Use structured output wherever possible.

Order extraction:

```json
{
    "intent": "food_order",
    "items": [
        {
            "dish_name": "burger",
            "quantity": 2
        }
    ]
}
```

Possible intent values:

```text
food_order
unrelated
incomplete_order
ambiguous
```

Partial-order decision:

```json
{
    "decision": "ACCEPT_PARTIAL"
}
```

or:

```json
{
    "decision": "NEW_ORDER"
}
```

or:

```json
{
    "decision": "AMBIGUOUS"
}
```

---

# 37. OPEN QUESTIONS

Before implementation, identify unresolved requirements.

If any requirement is genuinely ambiguous, ask a clarification question before coding.

Do NOT stop implementation for questions that have already been resolved by this specification.

The following decisions are already fixed:

```text
Order attempts = 3 total valid order submissions
Cook attempts = 2 total executions
Serve attempts = 2 total executions
Unrelated input = does not consume order attempt
Missing quantity = clarification, no attempt consumed
Menu checking = deterministic node/service
Retry routing = deterministic LangGraph routers
LLM = language understanding + response generation
```

---

# 38. TESTING STRATEGY

Testing must happen at three levels.

## 38.1 Unit Tests

Test each node independently.

Required tests include:

### Order parser

* Valid single-item order
* Valid multi-item order
* Different quantities
* Case-insensitive dish names
* Unrelated input
* Missing quantity
* Ambiguous order
* Invalid quantity
* Zero/negative quantity

### Order confirmation

* Fully available order
* Partially available order
* Completely unavailable order
* Unknown dish
* Multiple mixed availability items
* Exact inventory match
* Requested quantity greater than inventory

### User decision

* Accept partial
* Reject partial
* Ambiguous response

### Cook

* Success
* Failure with retry remaining
* Failure with no retry remaining

### Serve

* Success
* Failure with cook retry available
* Failure with cook retry exhausted
* Failure with serve retry exhausted

### Routers

Every status/counter combination must route correctly.

---

# 39. INTEGRATION TESTS

Test the entire LangGraph workflow.

At minimum:

```text
START → parser → confirmation → cook → serve → END
```

and all failure branches.

Use deterministic cook/serve simulators.

Do NOT use real randomness in integration tests.

---

# 40. SCENARIO TEST CASES

## TC01 — Unrelated Input + Partial Rejection + New Order Failure

### Sequence

1. User asks an unrelated question.
2. System explains that it is a restaurant ordering agent.
3. User places an order.
4. Order is partially available.
5. System asks whether to accept the partial order.
6. User rejects it.
7. User submits another order.
8. New order is unavailable.
9. No order attempts remain.
10. Workflow terminates.

### Expected

```text
final status = ORDER_FAILED
```

Important:

The unrelated question must NOT consume an order attempt.

Expected order-attempt behavior:

```text
valid order #1 → attempts remaining = 2
valid order #2 → attempts remaining = 1
```

If the specification interprets "3 attempts" as three valid submissions, the implementation must preserve the remaining third attempt unless the third order is actually submitted.

The test must therefore explicitly submit the third order if the intended behavior is exhaustion after three submitted orders.

---

# 41. TC01 CORRECTED DETERMINISTIC VERSION

To explicitly test exhaustion:

```text
Input 1: unrelated question
Input 2: partial order
Input 3: reject partial
Input 4: unavailable order
Input 5: another unavailable order
```

Expected:

```text
valid order attempt #1
valid order attempt #2
valid order attempt #3
ORDER_FAILED
```

The test should verify that no fourth valid order is accepted.

---

# 42. TC02 — Cook Failure + Recovery + Serve Failure + Recook

Initial state:

```text
order_attempts_remaining = 3
cook_attempts_remaining = 2
serve_attempts_remaining = 2
```

User submits a fully available order.

Expected execution:

```text
ORDER_CONFIRMED

COOK attempt #1
→ FAIL

COOK attempt #2
→ SUCCESS

SERVE attempt #1
→ FAIL

cook attempts remain?
→ NO

```

If the test requires the serve failure to trigger a cook retry, then the cook simulator must instead be configured so that one cook retry remains after the first successful cook.

Therefore the correct deterministic sequence for the stated requirement is:

```text
COOK #1 → SUCCESS
SERVE #1 → FAIL
COOK #2 → SUCCESS
SERVE #2 → SUCCESS
```

Expected:

```text
ORDER_COMPLETED
final_result.success = True
```

If the intended TC02 sequence is specifically:

```text
COOK #1 → FAIL
COOK #2 → SUCCESS
SERVE #1 → FAIL
COOK #3 → SUCCESS
```

then cook attempts must be changed from `2 total` to `3 total`.

Do not silently implement three cook attempts while the specification says two.

---

# 43. TC03 — Cook Exhaustion + Serve Retry

This scenario verifies that serving can use its remaining attempt without illegally invoking exhausted cook retries.

Sequence:

```text
ORDER_CONFIRMED

COOK #1 → FAIL
COOK #2 → SUCCESS

SERVE #1 → FAIL

cook_attempts_remaining == 0
```

Therefore:

```text
DO NOT CALL COOK
```

Instead:

```text
SERVE #2 → FAIL
```

Then:

```text
ORDER_FAILED
```

Expected:

```text
final_result.success = False
status = ORDER_FAILED
```

This test specifically verifies the invariant:

```text
cook_attempts_remaining never becomes negative
```

and:

```text
cook is never executed after its retry budget reaches zero
```

---

# 44. ADDITIONAL REQUIRED TEST CASES

## TC04 — Fully Available Immediate Success

```text
User order
→ fully available
→ cook success
→ serve success
→ ORDER_COMPLETED
```

---

## TC05 — Completely Unavailable

```text
User order
→ all items unavailable
→ ORDER_NA
→ user submits new order
→ new order fully available
→ cook
→ serve
→ ORDER_COMPLETED
```

---

## TC06 — Accept Partial Order

```text
User requests:
4 burgers

Available:
2 burgers

User:
"Yes, I'll take the 2."

Expected:
accepted_quantity = 2
→ COOK
→ SERVE
→ ORDER_COMPLETED
```

---

## TC07 — Unknown Dish

```text
User:
"I want 2 dragon burgers."

Menu:
dish does not exist
```

Expected:

```text
available_quantity = 0
status = ORDER_NA
```

---

## TC08 — Missing Quantity

```text
User:
"I want pizza."
```

Expected:

```text
clarification requested
```

No order attempt consumed until a valid order is produced.

---

## TC09 — Ambiguous Partial Decision

```text
System:
"We have only 2 burgers. Accept?"

User:
"Maybe."
```

Expected:

```text
AMBIGUOUS
```

System asks again.

No order retry consumed.

---

## TC10 — Cook Always Fails

```text
COOK #1 → FAIL
COOK #2 → FAIL
```

Expected:

```text
ORDER_FAILED
```

No third cook execution.

---

## TC11 — Serve Always Fails

```text
COOK → SUCCESS

SERVE #1 → FAIL
COOK unavailable/exhausted if applicable
SERVE #2 → FAIL
```

Expected:

```text
ORDER_FAILED
```

---

## TC12 — Retry Counter Integrity

Verify invariants:

```text
order_attempts_remaining >= 0
cook_attempts_remaining >= 0
serve_attempts_remaining >= 0
```

No counter may become negative.

---

## TC13 — New Order Does Not Reset Operational Retries

If:

```text
cook_attempts_remaining = 1
```

and user rejects a partial order and submits a new order, the cook counter MUST remain:

```text
1
```

It must not reset to:

```text
2
```

unless a completely new order session is explicitly started.

---

## TC14 — Successful Order Is Terminal

After:

```text
ORDER_COMPLETED
```

the graph MUST terminate.

It must not:

* Cook again
* Serve again
* Ask for another order
* Consume retry counters

---

# 45. PROPERTY / INVARIANT TESTING

Verify the following invariants throughout execution.

### Invariant 1

```text
cook_attempts_remaining >= 0
```

### Invariant 2

```text
serve_attempts_remaining >= 0
```

### Invariant 3

```text
order_attempts_remaining >= 0
```

### Invariant 4

No cook execution occurs when:

```text
cook_attempts_remaining == 0
```

### Invariant 5

No serve execution occurs when:

```text
serve_attempts_remaining == 0
```

### Invariant 6

No order attempt is consumed by unrelated input.

### Invariant 7

No inventory decision is made by the LLM.

### Invariant 8

No graph routing decision is made directly by the LLM.

### Invariant 9

A successful order always ends with:

```text
ORDER_COMPLETED
```

### Invariant 10

A terminal failed workflow always ends with:

```text
ORDER_FAILED
```

---

# 46. OBSERVABILITY

The implementation should make workflow execution easy to debug.

Log or expose:

```text
node entered
node exited
status transition
retry counter changes
order state
routing decision
error reason
```

Example:

```text
[ORDER_CONFIRMATION]
status: ORDER_RECEIVED -> ORDER_PARTIAL

[USER_DECISION]
decision: NEW_ORDER

[COOK]
attempt: 1/2
result: FAILED

[COOK]
attempt: 2/2
result: SUCCESS

[SERVE]
attempt: 1/2
result: FAILED

[ROUTER]
cook_attempts_remaining: 0
route: SERVE
```

Do not log sensitive information.

---

# 47. ERROR HANDLING

Distinguish between:

### Business failure

Examples:

```text
dish unavailable
cook failed
serve failed
```

and:

### System error

Examples:

```text
LLM API failure
inventory service failure
unexpected exception
malformed state
```

System errors should not be silently treated as ordinary business failures.

Create explicit error handling.

---

# 48. LLM FAILURE HANDLING

If structured LLM output cannot be parsed:

1. Do not mutate business state.
2. Do not consume operational retry counters.
3. Ask the user for clarification or retry the parsing operation according to the implementation policy.
4. Prevent malformed LLM output from entering the workflow.

Use schema validation.

---

# 49. SECURITY / ROBUSTNESS

User input must never directly become executable code.

Do not allow the LLM to modify:

```text
retry counters
status
inventory
routing
```

Validate all structured outputs.

Dish names should be normalized before inventory lookup.

Quantities must be positive integers.

---

# 50. IMPLEMENTATION ORDER

Implement in this order:

```text
1. Domain models
2. Shared state
3. Menu/inventory service
4. Order parser
5. Order confirmation
6. User decision handling
7. Cook simulator
8. Serve simulator
9. Response generation
10. Routers
11. LangGraph assembly
12. Unit tests
13. Integration tests
14. Scenario tests
15. Logging/observability
16. Final end-to-end verification
```

Do not build the entire system in one monolithic file.

---

# 51. TEST-FIRST REQUIREMENT

Before declaring the implementation complete:

1. Implement the state model.
2. Implement deterministic services.
3. Implement nodes.
4. Implement routers.
5. Implement tests.
6. Run all tests.
7. Inspect failures.
8. Correct implementation.
9. Re-run tests.
10. Repeat until all specified tests pass.

Do not modify tests simply to make incorrect implementation pass.

Tests may only be changed if the test itself contradicts the authoritative system specification.

---

# 52. REQUIRED FINAL VALIDATION

Before declaring Order-Pilot complete, verify:

```text
[ ] Modular architecture implemented
[ ] Shared state strongly typed
[ ] Messages use LangGraph message annotation
[ ] Order items represented as structured objects
[ ] Inventory is deterministic
[ ] LLM only handles language tasks
[ ] Routing is deterministic
[ ] Order retry limit enforced
[ ] Cook retry limit enforced
[ ] Serve retry limit enforced
[ ] Partial orders supported
[ ] New orders supported
[ ] Unknown dishes handled
[ ] Missing quantities handled
[ ] Unrelated questions handled
[ ] Cook failures tested
[ ] Serve failures tested
[ ] Cook exhaustion tested
[ ] Serve exhaustion tested
[ ] Terminal states verified
[ ] Retry counters never become negative
[ ] No illegal graph transitions
[ ] Deterministic test simulators implemented
[ ] TC01 passes
[ ] TC02 passes
[ ] TC03 passes
[ ] Additional tests pass
```

---

# 53. IMPORTANT IMPLEMENTATION RULE

Do not blindly follow contradictions in the original rough architecture.

When requirements conflict:

1. Preserve the core business intent.
2. Prefer deterministic and testable behavior.
3. Do not silently invent new behavior.
4. Document the ambiguity.
5. Resolve it through explicit state-machine rules.
6. Ensure the resulting implementation can be tested deterministically.

---

# 54. EXPECTED DELIVERABLE

The final implementation must contain:

```text
1. Complete modular Order-Pilot LangGraph implementation
2. Typed shared state
3. Deterministic inventory service
4. LLM order parser
5. Partial-order decision handler
6. Cook node
7. Serve node
8. Deterministic routers
9. User response generation
10. Retry management
11. Unit tests
12. Integration tests
13. End-to-end scenario tests
14. TC01
15. TC02
16. TC03
17. Additional edge-case tests
18. README with architecture explanation
19. Clear execution instructions
```

---

# 55. FINAL DESIGN PRINCIPLE

The system should follow this separation:

```text
                 NATURAL LANGUAGE
                       │
                       ▼
                    LLM
                       │
                       ▼
              STRUCTURED INTENT
                       │
                       ▼
              DETERMINISTIC STATE
                       │
                       ▼
             LANGGRAPH STATE MACHINE
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       INVENTORY      COOK         SERVE
          │            │            │
          └────────────┼────────────┘
                       ▼
                UPDATED STATE
                       │
                       ▼
                 DETERMINISTIC
                    ROUTER
                       │
                       ▼
                NEXT WORKFLOW
                     STEP
```

The fundamental rule is:

> **Use the LLM for language. Use LangGraph and deterministic application code for business logic, state transitions, retries, and workflow control.**

Build Order-Pilot according to this specification and run the complete test suite before considering the implementation finished.
