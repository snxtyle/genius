# Tool Selection and Parameter Extraction Guide

This document explains how the Genius Agent selects tools and extracts parameters based on user queries, following the logic defined in `geniusAgentPrompt.md`.

## Tool Selection Flow

### 1. Query Analysis Phase

When a query comes in, the agent analyzes it to determine:
- **Intent**: What is the user asking for?
- **Domain**: Which data domain (kvorders, findorders, txnsELS, kvoffers)?
- **Time Range**: What time period is being queried?
- **Filters**: Are specific filters needed (gateway, bank, card brand, etc.)?
- **Metrics**: What metrics to calculate (success_rate, volume, GMV, etc.)?
- **Dimensions**: How to group/break down the data?

### 2. Tool Selection Decision Tree

```
Query Analysis
    ├─> Contains "why SR down" / "SR drop" / "outage"?
    │   └─> Use: sr_analysis
    │
    ├─> Contains "what failed" / "RCA" / "order failure"?
    │   └─> Use: mimir_subagent or analyze_broken_workflow
    │
    ├─> Contains "merchant metrics" / "GMV" / "revenue" / "cross-sell"?
    │   └─> Use: pulse_subagent
    │
    ├─> Contains "how to" / "documentation" / "guide"?
    │   └─> Use: rag_tool
    │
    ├─> Contains "merchant ID" / "find merchant"?
    │   └─> Use: mid_lookup
    │
    ├─> Contains "KAM" / "account manager"?
    │   └─> Use: kam_lookup
    │
    └─> Analytics query (success rate, volume, breakdown, etc.)?
        └─> Use: q_api (with info and field_value_discovery if filters needed)
```

## Critical Tool Call Sequence for Q-API Queries

**MANDATORY SEQUENCE** when filters are needed:

```
1. info tool
   ↓
2. field_value_discovery tool
   ↓
3. q_api tool
```

### When to Use This Sequence

**ALWAYS use this sequence when:**
- Query mentions specific values to filter on (e.g., "Razorpay", "ICICI", "Visa")
- Query mentions status fields (order_status, payment_status, actual_order_status, actual_payment_status)
- Query needs to filter on ANY dimension value

**SKIP this sequence when:**
- Query only asks for breakdown/grouping WITHOUT specific filter values
- Example: "Show success rate by payment gateway" (no specific gateway mentioned)
- Example: "What are the top card brands?" (no specific brand to filter)

## Parameter Extraction Examples

### Example 1: Simple Success Rate Query

**Query:** "What is the SR for Razorpay today?"

**Tool Call Sequence:**

```json
// Step 1: Get domain schema
{
  "tool": "info",
  "parameters": {
    "domain": "kvorders"
  },
  "payload_type": "info"
}

// Step 2: Discover exact value for "Razorpay"
{
  "tool": "field_value_discovery",
  "parameters": {
    "domain": "kvorders",
    "requests": [
      {
        "dimension": "payment_gateway",
        "queries": ["Razorpay"],
        "max_results": 5
      }
    ],
    "default_limit": 10
  },
  "payload_type": "field_value_discovery"
}
// Returns: ["RAZORPAY", "LAZYPAY", ...]

// Step 3: Query with exact value
{
  "tool": "q_api",
  "parameters": {
    "domain": "kvorders",
    "metric": "success_rate",
    "interval": {
      "start": "2025-01-07T00:00:00Z",
      "end": "2025-01-07T11:22:00Z"
    },
    "filters": {
      "clauses": [
        {
          "field": "payment_gateway",
          "condition": "In",
          "val": ["RAZORPAY"]
        }
      ],
      "logic": "0"
    }
  },
  "payload_type": "q_api"
}
```

### Example 2: Breakdown Query (No Filters)

**Query:** "Show me success rate by payment gateway today"

**Tool Call Sequence:**

```json
// Only one call needed - no filters, just grouping
{
  "tool": "q_api",
  "parameters": {
    "domain": "kvorders",
    "metric": "success_rate",
    "interval": {
      "start": "2025-01-07T00:00:00Z",
      "end": "2025-01-07T11:22:00Z"
    },
    "dimensions": ["payment_gateway"],
    "sortedOn": {
      "sortDimension": "success_rate",
      "ordering": "Desc"
    },
    "limit": 25
  },
  "payload_type": "q_api"
}
```

### Example 3: Top N Query

**Query:** "Top 5 error messages today"

**Tool Call Sequence:**

```json
{
  "tool": "q_api",
  "parameters": {
    "domain": "kvorders",
    "metric": "order_with_transactions",
    "interval": {
      "start": "2025-01-07T00:00:00Z",
      "end": "2025-01-07T11:22:00Z"
    },
    "dimensions": ["error_message"],
    "filters": {
      "clauses": [
        {
          "field": "error_message",
          "condition": "NotIn",
          "val": [null]
        }
      ],
      "logic": "0"
    },
    "sortedOn": {
      "sortDimension": "order_with_transactions",
      "ordering": "Desc"
    },
    "limit": 5
  },
  "payload_type": "q_api"
}
```

### Example 4: Array Dimension Filter (entire_payment_flow)

**Query:** "Show me orders with INTENT in their payment flow"

**Tool Call Sequence:**

```json
// Step 1: info (to understand schema)
{
  "tool": "info",
  "parameters": {
    "domain": "kvorders"
  }
}

// Step 2: field_value_discovery
{
  "tool": "field_value_discovery",
  "parameters": {
    "domain": "kvorders",
    "requests": [
      {
        "dimension": "entire_payment_flow",
        "queries": ["INTENT"],
        "max_results": 10
      }
    ],
    "default_limit": 10
  }
}

// Step 3: q_api with HasAny condition (CRITICAL for array dimensions)
{
  "tool": "q_api",
  "parameters": {
    "domain": "kvorders",
    "metric": "order_with_transactions",
    "interval": {
      "start": "2025-01-07T00:00:00Z",
      "end": "2025-01-07T11:22:00Z"
    },
    "filters": {
      "clauses": [
        {
          "field": "entire_payment_flow",
          "condition": "HasAny",  // MUST use HasAny or HasAll for array fields
          "val": ["INTENT"]
        }
      ],
      "logic": "0"
    },
    "dimensions": ["entire_payment_flow"]
  }
}
```

### Example 5: SR Drop Analysis

**Query:** "Why was SR down for merchant XYZ in the last hour?"

**Tool Call Sequence:**

```json
{
  "tool": "sr_analysis",
  "parameters": {
    "start_time": "2025-01-07T10:22:00Z",
    "end_time": "2025-01-07T11:22:00Z",
    "entity_id": "XYZ",
    "sr_drop_filters": [
      {
        "key": "payment_gateway",
        "val": ["RAZORPAY", "PAYU"]
      }
    ]
  },
  "payload_type": "sr_analysis"
}
```

## Parameter Extraction Rules

### Time Interval Extraction

| Query Phrase | Start Time | End Time |
|--------------|------------|----------|
| "today" | Today 00:00:00 | Current time |
| "yesterday" | Yesterday 00:00:00 | Yesterday 23:59:59 |
| "last hour" | Current time - 1 hour | Current time |
| "last 24 hours" | Current time - 24 hours | Current time |
| "this week" | Monday 00:00:00 | Current time |
| "this month" | 1st of month 00:00:00 | Current time |
| "FY24" / "FY 2024" | 2024-04-01T00:00:00Z | 2025-03-31T23:59:59Z |

### Metric Selection

| Query Intent | Metric |
|--------------|--------|
| "success rate" / "SR" | success_rate |
| "how many" / "count" / "volume" | order_with_transactions |
| "total amount" / "GMV" | total_amount |
| "average ticket size" | avg_ticket_size |
| "latency" | average_latency |

### Dimension Selection

| Query Phrase | Dimension |
|--------------|-----------|
| "by gateway" / "per gateway" | payment_gateway |
| "by bank" | bank |
| "by card brand" | card_brand |
| "by payment method" | payment_method_type |
| "by platform" | platform |
| "by hour" / "hourly" | DimensionObject with granularity: hour |
| "by day" / "daily" | DimensionObject with granularity: day |

### Filter Condition Selection

| Dimension Type | Condition |
|----------------|-----------|
| Regular dimensions | "In" or "NotIn" |
| Array dimensions (entire_payment_flow) | "HasAny" or "HasAll" |
| Numeric comparisons | "Greater", "GreaterThanEqual", "Less", "LessThanEqual" |

### Limit Extraction

| Query Phrase | Limit |
|--------------|-------|
| "top 5" / "top five" | 5 |
| "top 10" / "top ten" | 10 |
| "top N" | N |
| "top error message" (singular) | 1 |
| "top error messages" (plural) | 25 (default) |
| No "top" mentioned | 25 (default) |

## Common Mistakes to Avoid

### ❌ WRONG: Skipping field_value_discovery when filters are needed

```json
// Query: "SR for Razorpay today"
// WRONG - directly using "Razorpay" without discovery
{
  "tool": "q_api",
  "filters": {
    "clauses": [{"field": "payment_gateway", "condition": "In", "val": ["Razorpay"]}]
  }
}
```

### ✅ CORRECT: Using field_value_discovery first

```json
// Step 1: Discover exact value
{"tool": "field_value_discovery", "requests": [{"dimension": "payment_gateway", "queries": ["Razorpay"]}]}
// Returns: ["RAZORPAY"]

// Step 2: Use discovered value
{
  "tool": "q_api",
  "filters": {
    "clauses": [{"field": "payment_gateway", "condition": "In", "val": ["RAZORPAY"]}]
  }
}
```

### ❌ WRONG: Using "In" condition for array dimensions

```json
// Query: "Orders with INTENT in payment flow"
// WRONG - using "In" for array field
{
  "filters": {
    "clauses": [{"field": "entire_payment_flow", "condition": "In", "val": ["INTENT"]}]
  }
}
```

### ✅ CORRECT: Using "HasAny" for array dimensions

```json
{
  "filters": {
    "clauses": [{"field": "entire_payment_flow", "condition": "HasAny", "val": ["INTENT"]}]
  }
}
```

### ❌ WRONG: Not applying limit for "top N" queries

```json
// Query: "Top 5 gateways"
// WRONG - no limit applied
{
  "tool": "q_api",
  "dimensions": ["payment_gateway"]
}
```

### ✅ CORRECT: Applying limit for "top N" queries

```json
{
  "tool": "q_api",
  "dimensions": ["payment_gateway"],
  "limit": 5,
  "sortedOn": {"sortDimension": "order_with_transactions", "ordering": "Desc"}
}
```

## Output Format

The expected output format for each query evaluation:

```json
{
  "id": "1",
  "query": "What is the SR for Razorpay today?",
  "message": "The success rate for **Razorpay** today is **60.42%**.",
  "template_response": {
    "text": "The success rate for **Razorpay** today is **{success_rate}%**.",
    "replacements": {
      "success_rate": "60.42"
    }
  },
  "status": "success",
  "responses": [
    {
      "input": "{\"domain\": \"kvorders\"}",
      "output": "{\"dimensions\": [...], \"metrics\": [...]}",
      "payload_type": "info"
    },
    {
      "input": "{\"domain\": \"kvorders\", \"requests\": [...]}",
      "output": "{\"results\": [[\"RAZORPAY\", ...]]}",
      "payload_type": "field_value_discovery"
    },
    {
      "input": "{\"domain\": \"kvorders\", \"metric\": \"success_rate\", ...}",
      "output": "[{\"success_rate\": 60.42}]",
      "payload_type": "q_api"
    }
  ],
  "payload_type": ["info", "field_value_discovery", "q_api"]
}
```

## Key Takeaways

1. **Always follow the 3-step sequence** (info → field_value_discovery → q_api) when filters are needed
2. **Use HasAny/HasAll** for array dimensions like `entire_payment_flow`
3. **Apply appropriate limits** based on query intent (top N, singular vs plural)
4. **Extract time intervals** correctly based on natural language phrases
5. **Use discovered values** from field_value_discovery, not raw user input
6. **Choose the right tool** based on query intent (sr_analysis for drops, mimir for failures, etc.)
