# Genius Agent Tools - Comprehensive Input Parameters Documentation

This document provides an exhaustive list of all tools available in the Genius agent and their possible input parameters with types.

## Core Analytics Tools

### 1. sr_analysis
**Description:** Analyze service request drops for a merchant over a specified time period.

**All possible input params for tool:**
- `start_time`: `datetime` - Start time for the SR analysis period (required)
- `end_time`: `datetime` - End time for the SR analysis period (required)
- `sr_drop_filters`: `Optional[Union[SRFilter, List[SRFilter]]]` - Optional filters to apply to the SR drop analysis
- `entity_id`: `Optional[str]` - Merchant ID to analyze (required for execution)

**SRFilter Type Details:**
- `key`: FilterFieldLiteral - One of: "payment_gateway", "ticket_size", "actual_payment_status", "auth_type", "card_brand", "payment_method_type", "payment_method_subtype", "payment_instrument_group", "is_tokenized", "txn_flow_type", "txn_type", "txn_object_type", "txn_latency_enum", "payment_flow", "emi_type", "order_type", "is_upicc", "is_emi", "bank", "error_message", "gateway_reference_id"
- `val`: `Union[str, int, float, bool, List[Union[str, int, float, bool]]]` - Filter value(s)

### 2. math
**Description:** Perform mathematical calculations and evaluate arithmetic expressions safely.

**All possible input params for tool:**
- `expression`: `Union[str, List[str]]` - Mathematical expression(s) to evaluate (required)
- `variables`: `Dict[str, Union[float, List[float]]]` - Dictionary of variables to use in expression evaluation (default: {})
- `precision`: `Union[int, None]` - Number of decimal places to round results to (optional)

### 3. rag_tool
**Description:** Query the RAG (Retrieval Augmented Generation) system using Vertex AI.

**All possible input params for tool:**
- `query`: `str` - The question to ask the RAG system (required)
- `similarity_top_k`: `int` - Number of similar documents to retrieve from knowledge base (default: 20)

### 4. search_memory
**Description:** Search through conversation memory and historical data.

**All possible input params for tool:**
- `query`: `str` - Search query for memory lookup (required)
- `limit`: `int` - Maximum number of results to return (optional)

## Q-API Tools

### 5. q_api
**Description:** Execute multi-domain analytics queries against the Q-API system.

**All possible input params for tool:**
- `domain`: `str` - Target domain for the query (required)
- `metric`: `Union[str, List[str]]` - Metric(s) to query (required)
- `interval`: `Interval` - Time interval for the query (required)
- `filters`: `Optional[FlatFilter]` - Filters to apply to the query (optional)
- `dimensions`: `List[Union[str, DimensionObject]]` - Dimensions for grouping (default: [])
- `sortedOn`: `Optional[object]` - Sorting configuration (optional)
- `metric_filters`: `Optional[List[MetricFilter]]` - Filters for aggregated metrics (optional)
- `limit`: `Optional[int]` - Maximum number of results (default: 100)

**Complex Type Details:**

**Interval:**
- `start`: `str` - Start time in format "%Y-%m-%dT%H:%M:%SZ" (required)
- `end`: `str` - End time in format "%Y-%m-%dT%H:%M:%SZ" (required)

**FlatFilter:**
- `clauses`: `List[Clause]` - List of filter clauses (1-10 items, required)
- `logic`: `str` - Boolean logic expression referencing clause indices (required)

**Clause:**
- `field`: `str` - Dimension field name (required)
- `condition`: FilterCondition - One of: "In", "NotIn", "Greater", "GreaterThanEqual", "LessThanEqual", "Less", "HasAny", "HasAll"
- `val`: `Union[str, bool, float, None, List[Union[str, bool, None]]]` - Filter value(s) (required)

**MetricFilter:**
- `metric`: `str` - Metric name (required)
- `condition`: MetricCondition - One of: "Greater", "GreaterThanEqual", "LessThanEqual", "Less"
- `value`: `Union[int, float]` - Filter value (required)

**DimensionObject:**
- `granularity`: `Granularity` - Time granularity configuration (required)
- `intervalCol`: Literal - One of: "order_created_at", "refund_date", "offer_date_created", "notification_date_created", "fulfillment_created_at"
- `timeZone`: Literal["Asia/Kolkata"] - Timezone (required)

**Granularity:**
- `unit`: Literal - One of: "second", "minute", "hour", "day", "week", "month"
- `duration`: `int` - Duration value (≥1, required)

### 6. info
**Description:** Get available dimensions, metrics, and filters for a specific domain.

**All possible input params for tool:**
- `domain`: `str` - Domain to get information about (required)

### 7. field_value_discovery
**Description:** Discover possible values for specific fields/dimensions in a domain.

**All possible input params for tool:**
- `domain`: `str` - Target domain (required)
- `requests`: `List[DimensionLookupRequest]` - List of dimension lookup requests (required)
- `default_limit`: `int` - Default limit for results (required)

**DimensionLookupRequest:**
- `dimension`: `str` - The dimension to look up values for (required)
- `queries`: `List[str]` - List of fuzzy search queries (required)
- `max_results`: `Optional[int]` - Maximum results per query (optional)


## Lookup Tools (JUSPAY Context Only)

### 9. mid_lookup
**Description:** Tool to find a definitive Merchant ID (MID) or suggest options based on fuzzy search.

**All possible input params for tool:**
- `merchant_name_query`: `str` - Merchant name or identifier to search for in the MID database (required)

### 10. kam_lookup
**Description:** Look up the Key Account Manager (KAM) username for a given Merchant ID.

**All possible input params for tool:**
- `mid`: `str` - The Merchant ID (MID) to look up the KAM for (required)

## Data Analysis Tools

### 11. q_api_csv
**Description:** Export Q-API query results to CSV format.

**All possible input params for tool:**
- `query_payload`: `QApiPayload` - Q-API query configuration (required)
- `filename`: `Optional[str]` - Output filename (optional)

### 12. sr_recommendations
**Description:** Generate service request improvement recommendations.

**All possible input params for tool:**
- `merchant_id`: `str` - Merchant ID to analyze (required)
- `time_period`: `Optional[str]` - Analysis time period (optional)

### 13. display_message
**Description:** Display formatted messages to users.

**All possible input params for tool:**
- `message`: `str` - Message content to display (required)
- `message_type`: `Optional[str]` - Type of message (info, warning, error) (optional)

## Workflow Analysis Tools (Mimir)

### 14. analyze_broken_workflow
**Description:** Analyze broken payment workflows and identify failure points for specific orders.

**All possible input params for tool:**
- `order_id`: `str` - Unique identifier for the payment order to analyze (required)
- `entity_id`: `Optional[str]` - Entity identifier (defaults to merchantId from token if not provided)
- `entity_context`: `Optional[str]` - Context type (extracted from token response if not provided)
- `merchant_id`: `Optional[str]` - Merchant ID (defaults to merchantId from token if not provided)
- `query`: `Optional[str]` - Optional problem statement to be passed to the agent

### 15. analyze_refund_workflow
**Description:** Analyze refund payment workflows and identify failure points for specific refunds.

**All possible input params for tool:**
- `refund_id`: `str` - Unique identifier for the payment refund to analyze (required)
- `entity_id`: `Optional[str]` - Entity identifier (defaults to merchantId from token if not provided)
- `entity_context`: `Optional[str]` - Context type (extracted from token response if not provided)

### 16. get_stream_response
**Description:** Retrieve AI assistant analysis responses from previous conversations.

**All possible input params for tool:**
- `unified_thread_id`: `str` - Combined thread ID in format "asst_XXX___thread_YYY" (required)
- `should_stream`: `bool` - Whether to retrieve streaming response format (default: False)
- `entity_id`: `Optional[str]` - Entity identifier (defaults to merchantId from token if not provided)
- `entity_context`: `Optional[str]` - Context type (extracted from token response if not provided)

## Sub-Agents

### 17. mimir_subagent
**Description:** Comprehensive Mimir workflow analysis agent.

**All possible input params for tool:**
- `query`: `str` - Analysis query or request (required)
- `analysis_type`: `Optional[str]` - Type of analysis to perform (optional)

### 18. pulse_subagent
**Description:** Business intelligence and merchant analytics agent.

**All possible input params for tool:**
- `query`: `str` - Business intelligence query (required)
- `merchant_context`: `Optional[str]` - Merchant context for analysis (optional)

### 19. sr_analysis_subagent
**Description:** Specialized service request analysis agent.

**All possible input params for tool:**
- `query`: `str` - SR analysis query (required)
- `merchant_id`: `Optional[str]` - Target merchant ID (optional)
- `time_range`: `Optional[str]` - Analysis time range (optional)

## Pulse Business Intelligence Tools

### 20. analyze_bd_team_details
**Description:** Retrieve Business Development team details from Pulse API.

**All possible input params for tool:**
- No input parameters required (authentication handled automatically)

### 21. analyze_merchant_metrics
**Description:** Analyze merchant performance metrics and key indicators.

**All possible input params for tool:**
- `merchant_id`: `Optional[str]` - Specific merchant to analyze (optional)
- `time_period`: `Optional[str]` - Time period for analysis (optional)

### 22. analyze_industry_merchant_mapping
**Description:** Analyze merchant distribution and mapping across industries.

**All possible input params for tool:**
- `industry`: `Optional[str]` - Specific industry to focus on (optional)
- `region`: `Optional[str]` - Geographic region filter (optional)

### 23. analyze_organization_product_usage
**Description:** Analyze product usage patterns across organization.

**All possible input params for tool:**
- `product_type`: `Optional[str]` - Specific product to analyze (optional)
- `time_range`: `Optional[str]` - Analysis time range (optional)

### 24. analyze_merchant_payment_split
**Description:** Analyze payment method distribution for merchants.

**All possible input params for tool:**
- `merchant_id`: `Optional[str]` - Target merchant for analysis (optional)
- `date_range`: `Optional[str]` - Date range for analysis (optional)

### 25. analyze_organization_merchant_mapping
**Description:** Analyze merchant mapping within organization structure.

**All possible input params for tool:**
- `organization_id`: `Optional[str]` - Organization to analyze (optional)
- `hierarchy_level`: `Optional[str]` - Organizational level to focus on (optional)

### 26. analyze_cross_selling_opportunities
**Description:** Identify cross-selling opportunities across merchant base.

**All possible input params for tool:**
- `merchant_segment`: `Optional[str]` - Merchant segment to analyze (optional)
- `product_focus`: `Optional[str]` - Product area for cross-selling (optional)

### 27. analyze_merchant_revenue_trends
**Description:** Analyze revenue trends for specific merchants.

**All possible input params for tool:**
- `merchant_id`: `Optional[str]` - Merchant to analyze (optional)
- `trend_period`: `Optional[str]` - Period for trend analysis (optional)

### 28. analyze_all_merchants_revenue
**Description:** Analyze revenue patterns across all merchants.

**All possible input params for tool:**
- `aggregation_level`: `Optional[str]` - Level of aggregation (optional)
- `time_window`: `Optional[str]` - Time window for analysis (optional)

### 29. analyze_specific_merchant_revenue
**Description:** Detailed revenue analysis for a specific merchant.

**All possible input params for tool:**
- `merchant_id`: `str` - Specific merchant ID to analyze (required)
- `analysis_depth`: `Optional[str]` - Depth of analysis (optional)

## External MCP Tools

### 30. Juspay Dashboard MCP Tools 


### 30. Juspay MCP Tools

### juspay_list_configured_gateway
**All possible input params for tool:**
- `merchantId`: `Optional[str]` - Merchant identifier for which to list configured payment gateways.

### juspay_get_gateway_scheme
**All possible input params for tool:**
- `gateway`: `str` - Gateway code (e.g., 'TATA_PA') for which to fetch detailed configuration information.
- `merchantId`: `Optional[str]` - Merchant identifier (optional, but recommended for context).

### juspay_get_gateway_details
**All possible input params for tool:**
- `mga_id`: `int` - The MGA ID of the gateway (from list_configured_gateways).
- `merchantId`: `str` - Merchant identifier for which to get gateway details.

### juspay_list_gateway_scheme
**All possible input params for tool:**
- No input parameters required.

### juspay_get_merchant_gateways_pm_details
**All possible input params for tool:**
- No input parameters required.

### juspay_get_offer_details
**All possible input params for tool:**
- `offer_ids`: `List[str]` - List of unique identifiers of the offers to retrieve details for.
- `merchant_id`: `str` - Merchant ID associated with the offer.
- `is_batch`: `Optional[bool]` - Whether this is a batch offer (default: False).

### juspay_list_offers
**All possible input params for tool:**
- `merchant_id`: `str` - Merchant identifier for which to list offers.
- `created_at`: `Optional[Dict[str, str]]` - Created at filter with 'lte' and 'gte' string timestamps (ISO 8601 format). Auto-generated from start_time and end_time if not provided.
- `start_time`: `str` - Start time for filtering offers (ISO format).
- `end_time`: `str` - End time for filtering offers (ISO format).
- `limit`: `Optional[int]` - Limit for number of offers to fetch.
- `sort_offers`: `SortOffersOptions` - Sorting options for offers. Example: {'field': 'CREATED_AT', 'order': 'DESCENDING'}

### juspay_get_user
**All possible input params for tool:**
- `userId`: `str` - Unique identifier for the user to retrieve.

### juspay_list_users_v2
**All possible input params for tool:**
- `offset`: `Optional[int]` - Pagination offset for the user list (default: 0).

### juspay_get_conflict_settings
**All possible input params for tool:**
- No input parameters required.

### juspay_get_general_settings
**All possible input params for tool:**
- No input parameters required.

### juspay_get_mandate_settings
**All possible input params for tool:**
- `merchantId`: `Optional[str]` - Optional merchant ID to retrieve mandate settings for.

### juspay_get_priority_logic_settings
**All possible input params for tool:**
- No input parameters required.

### juspay_get_routing_settings
**All possible input params for tool:**
- No input parameters required.

### juspay_get_webhook_settings
**All possible input params for tool:**
- No input parameters required.

### juspay_get_order_details
**All possible input params for tool:**
- `order_id`: `str` - Order ID for which details are to be fetched.

### juspay_list_payment_links_v1
**All possible input params for tool:**
- `qFilters`: `Optional[Dict[str, Any]]` - Q API filters for payment links.
- `date_from`: `str` - Start date/time in ISO 8601 format.
- `date_to`: `str` - End date/time in ISO 8601 format.
- `offset`: `Optional[int]` - Pagination offset (default: 0).

### create_payment_link_juspay
**All possible input params for tool:**
- `amount`: `Union[int, float]` - Payment amount (required).
- `payment_page_client_id`: `Optional[str]` - Client ID for payment page.
- `currency`: `Optional[str]` - Payment currency (default: "INR").
- `mobile_country_code`: `Optional[str]` - Mobile country code (default: "+91").
- `customer_email`: `Optional[str]` - Customer email address.
- `customer_phone`: `Optional[str]` - Customer phone number.
- `customer_id`: `Optional[str]` - Unique customer identifier.
- `order_id`: `Optional[str]` - Unique order identifier.
- `return_url`: `Optional[str]` - URL to redirect after payment.
- `gateway_id`: `Optional[str]` - Gateway identifier.
- `merchant_id`: `Optional[str]` - Merchant identifier.
- `walletCheckBox`: `Optional[bool]` - Enable wallet payment option.
- `cardsCheckBox`: `Optional[bool]` - Enable cards payment option.
- `netbankingCheckBox`: `Optional[bool]` - Enable netbanking payment option.
- `upiCheckBox`: `Optional[bool]` - Enable UPI payment option.
- `consumerFinanceCheckBox`: `Optional[bool]` - Enable consumer finance option.
- `otcCheckBox`: `Optional[bool]` - Enable OTC payment option.
- `virtualAccountCheckBox`: `Optional[bool]` - Enable virtual account option.
- `shouldSendMail`: `Optional[bool]` - Whether to send email notification.
- `shouldSendSMS`: `Optional[bool]` - Whether to send SMS notification.
- `shouldSendWhatsapp`: `Optional[bool]` - Whether to send WhatsApp notification.
- `showEmiOption`: `Optional[bool]` - Whether to show EMI options.
- `standardEmi`: `Optional[bool]` - Enable standard EMI.
- `standard_credit`: `Optional[bool]` - Enable standard credit EMI.
- `standard_debit`: `Optional[bool]` - Enable standard debit EMI.
- `standard_cardless`: `Optional[bool]` - Enable standard cardless EMI.
- `lowCostEmi`: `Optional[bool]` - Enable low cost EMI.
- `low_cost_credit`: `Optional[bool]` - Enable low cost credit EMI.
- `low_cost_debit`: `Optional[bool]` - Enable low cost debit EMI.
- `low_cost_cardless`: `Optional[bool]` - Enable low cost cardless EMI.
- `noCostEmi`: `Optional[bool]` - Enable no cost EMI.
- `no_cost_credit`: `Optional[bool]` - Enable no cost credit EMI.
- `no_cost_debit`: `Optional[bool]` - Enable no cost debit EMI.
- `no_cost_cardless`: `Optional[bool]` - Enable no cost cardless EMI.
- `showOnlyEmiOption`: `Optional[bool]` - Show only EMI options.
- `mandate_max_amount`: `Optional[str]` - Maximum mandate amount.
- `mandate_frequency`: `Optional[str]` - Mandate frequency.
- `mandate_start_date`: `Optional[str]` - Mandate start date.
- `mandate.revokable_by_customer`: `Optional[bool]` - Whether mandate is revokable by customer.
- `mandate.block_funds`: `Optional[bool]` - Whether to block funds for mandate.
- `mandate.frequency`: `Optional[str]` - Mandate frequency (dot notation).
- `mandate.start_date`: `Optional[str]` - Mandate start date (dot notation).
- `mandate.end_date`: `Optional[str]` - Mandate end date (dot notation).
- `subventionAmount`: `Optional[Union[str, int, None]]` - Subvention amount.
- `selectUDF`: `Optional[List[str]]` - Selected UDF fields.
- `offer_details`: `Optional[Union[Dict[str, Any], None]]` - Offer details.
- `options.create_mandate`: `Optional[str]` - Mandate creation option (dot notation).
- `options`: `Optional[Options]` - Options configuration.
- `payment_filter`: `Optional[PaymentFilter]` - Payment filter configuration.
- `metaData`: `Optional[Dict[str, Any]]` - Additional metadata.

### create_autopay_link_juspay
**All possible input params for tool:**
- `amount`: `Union[int, float]` - One-time payment amount (required).
- `payment_page_client_id`: `Optional[str]` - Client ID for payment page.
- `mandate_max_amount`: `str` - Max mandate amount for future payments (required).
- `mandate_start_date`: `str` - Mandate creation date (required).
- `mandate_end_date`: `str` - Future date after which mandate stops (required).
- `mandate_frequency`: `str` - Payment frequency (required).
- `currency`: `Optional[str]` - Payment currency (default: "INR").
- `mobile_country_code`: `Optional[str]` - Mobile country code (default: "+91").
- `customer_email`: `Optional[str]` - Customer email address.
- `customer_phone`: `Optional[str]` - Customer phone number.
- `customer_id`: `Optional[str]` - Unique customer identifier.
- `order_id`: `Optional[str]` - Unique order identifier.
- `return_url`: `Optional[str]` - URL to redirect after payment.
- `gateway_id`: `Optional[str]` - Gateway identifier.
- `merchant_id`: `Optional[str]` - Merchant identifier.
- `walletCheckBox`: `Optional[bool]` - Enable wallet payment option.
- `cardsCheckBox`: `Optional[bool]` - Enable cards payment option.
- `netbankingCheckBox`: `Optional[bool]` - Enable netbanking payment option.
- `upiCheckBox`: `Optional[bool]` - Enable UPI payment option.
- `consumerFinanceCheckBox`: `Optional[bool]` - Enable consumer finance option.
- `otcCheckBox`: `Optional[bool]` - Enable OTC payment option.
- `virtualAccountCheckBox`: `Optional[bool]` - Enable virtual account option.
- `shouldSendMail`: `Optional[bool]` - Whether to send email notification.
- `shouldSendSMS`: `Optional[bool]` - Whether to send SMS notification.
- `shouldSendWhatsapp`: `Optional[bool]` - Whether to send WhatsApp notification.
- `showEmiOption`: `Optional[bool]` - Whether to show EMI options.
- `standardEmi`: `Optional[bool]` - Enable standard EMI.
- `standard_credit`: `Optional[bool]` - Enable standard credit EMI.
- `standard_debit`: `Optional[bool]` - Enable standard debit EMI.
- `standard_cardless`: `Optional[bool]` - Enable standard cardless EMI.
- `lowCostEmi`: `Optional[bool]` - Enable low cost EMI.
- `low_cost_credit`: `Optional[bool]` - Enable low cost credit EMI.
- `low_cost_debit`: `Optional[bool]` - Enable low cost debit EMI.
- `low_cost_cardless`: `Optional[bool]` - Enable low cost cardless EMI.
- `noCostEmi`: `Optional[bool]` - Enable no cost EMI.
- `no_cost_credit`: `Optional[bool]` - Enable no cost credit EMI.
- `no_cost_debit`: `Optional[bool]` - Enable no cost debit EMI.
- `no_cost_cardless`: `Optional[bool]` - Enable no cost cardless EMI.
- `showOnlyEmiOption`: `Optional[bool]` - Show only EMI options.
- `mandate.revokable_by_customer`: `Optional[bool]` - Whether mandate is revokable by customer.
- `mandate.block_funds`: `Optional[bool]` - Whether to block funds for mandate.
- `mandate.frequency`: `Optional[str]` - Mandate frequency (dot notation).
- `mandate.start_date`: `Optional[str]` - Mandate start date (dot notation).
- `mandate.end_date`: `Optional[str]` - Mandate end date (dot notation).
- `subventionAmount`: `Optional[Union[str, int, None]]` - Subvention amount.
- `selectUDF`: `Optional[List[str]]` - Selected UDF fields.
- `offer_details`: `Optional[Union[Dict[str, Any], None]]` - Offer details.
- `options.create_mandate`: `Optional[str]` - Mandate creation option (dot notation).
- `options`: `Optional[Options]` - Options configuration.
- `payment_filter`: `Optional[PaymentFilter]` - Payment filter configuration.
- `metaData`: `Optional[Dict[str, Any]]` - Additional metadata.

### juspay_list_surcharge_rules
**All possible input params for tool:**
- No input parameters required.

### list_outages_juspay
**All possible input params for tool:**
- `startTime`: `str` - Start time in ISO format (e.g., '2025-05-22T18:30:00Z').
- `endTime`: `str` - End time in ISO format (e.g., '2025-05-23T10:30:12Z').
- `merchantId`: `Optional[str]` - Merchant ID to filter outages (optional).


## Parameter Type Definitions Summary

### Basic Types
- `str` - String values
- `int` - Integer values  
- `float` - Floating point values
- `bool` - Boolean values
- `datetime` - Python datetime objects
- `Optional[T]` - Optional type T (can be None)
- `Union[T1, T2]` - Either type T1 or T2
- `List[T]` - List of type T items
- `Dict[K, V]` - Dictionary with keys of type K and values of type V

### Literal Types
- Specific string values that are allowed (e.g., `Literal["In", "NotIn", "Greater"]`)

### Complex Model Types
- `SRFilter` - Service request filter configuration
- `QApiPayload` - Q-API query configuration
- `Interval` - Time interval specification
- `FlatFilter` - Boolean filter tree
- `Clause` - Individual filter clause
- `MetricFilter` - Metric-based filter
- `DimensionObject` - Time dimension configuration
- `Granularity` - Time granularity settings
- `DimensionLookupRequest` - Field value discovery request

## Notes

1. **Context Parameter**: All Genius tools automatically receive a `context` parameter that contains session information, authentication tokens, and other runtime data. This parameter is injected by the Genius framework and doesn't need to be provided explicitly.

2. **Optional vs Required**: Parameters marked as `Optional[T]` can be omitted or set to `None`. All other parameters are required unless they have default values specified.

3. **Type Validation**: Genius tools use Pydantic for parameter validation, ensuring type safety and providing helpful error messages for invalid inputs.

4. **Dynamic Tools**: MCP tools and sub-agents may have varying parameters depending on their specific implementation and capabilities.

5. **JUSPAY Context**: Some tools (mid_lookup, kam_lookup) are only available when `context_value` is set to "JUSPAY" in the agent configuration.

This documentation covers all tools currently available in the Genius agent as of the latest codebase analysis.
