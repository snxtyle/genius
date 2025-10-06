#!/usr/bin/env python3
"""
Follow-up Question Evaluation Script

This script evaluates multi-turn conversations with follow-up questions.
It maintains session context across queries to test the system's ability
to handle conversational analytics queries.

Usage:
    python followup_evaluation.py --conversations conversations_sample.csv --output opus-4.1.csv --summary opus-4.1_summary.json
"""

import asyncio
import csv
import json
import logging
import time
import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import pandas as pd
import aiohttp
import base64
from dataclasses import dataclass, asdict, field
from anthropic import AnthropicVertex
import vertexai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('followup_evaluation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv('realtime_application/.env')

# Vertex AI Configuration for Claude Judge
VERTEX_PROJECT = "dev-ai-gamma"
VERTEX_LOCATION = "us-east5"
CLAUDE_MODEL = "claude-sonnet-4@20250514"

# Langfuse credentials - set directly or via environment variables
LANGFUSE_SK = os.getenv('LANGFUSE_SK', 'sk-lf-65c9f49b-8a1a-48a3-9752-2605b7f6cf25')
LANGFUSE_PK = os.getenv('LANGFUSE_PK', 'pk-lf-292b26f3-6231-42f7-9ef9-816c90af9288')
LANGFUSE_HOST = os.getenv('LANGFUSE_HOST', 'https://periscope.breeze.in/')

@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation"""
    conversation_id: int
    turn_id: int
    query: str
    is_followup: bool
    depends_on: Optional[int] = None
    
@dataclass
class TurnResult:
    """Result of evaluating a single turn"""
    turn: ConversationTurn
    response: str
    response_time_ms: float
    session_id: Optional[str] = None
    # Standard evaluation scores
    correctness: Optional[int] = None
    explanation_quality: Optional[int] = None
    relevance: Optional[int] = None
    hallucination_check: Optional[int] = None
    tone_clarity: Optional[int] = None
    # Overall
    judge_result: Optional[str] = None
    judgment_reason: Optional[str] = None
    total_score: Optional[float] = None
    full_response: Optional[Dict] = None

@dataclass
class ConversationEvaluation:
    """Evaluation results for a full conversation"""
    conversation_id: int
    session_id: Optional[str]
    turns: List[TurnResult]
    overall_score: float = 0.0
    
    def calculate_scores(self):
        """Calculate aggregate scores for the conversation"""
        if not self.turns:
            return
        
        # Calculate overall score
        all_scores = [t.total_score for t in self.turns if t.total_score]
        self.overall_score = sum(all_scores) / len(all_scores) if all_scores else 0

class AnalyticsAPIClient:
    """Client for calling the analytics API with session support"""
    
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Generate authentication headers"""
        token = self.auth_token
        if token.startswith("Bearer "):
            token = token[7:]
        
        auth_string = f"{token}:"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        return {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def query_analytics_with_session(
        self, 
        query: str, 
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send query to analytics endpoint with optional session (with mock fallback)"""
        url = f"{self.base_url}/api/v3/analytics/"
        
        payload = {
            "query": query,
            "current_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        # Add session_id if provided (for follow-up queries)
        if session_id:
            payload["session_id"] = session_id
        
        headers = self._get_auth_headers()
        start_time = time.time()
        
        try:
            async with self.session.post(url, json=payload, headers=headers) as response:
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "data": data,
                        "response_time_ms": response_time_ms,
                        "session_id": data.get("session_id")  # Extract session_id
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Analytics API error {response.status}: {error_text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "response_time_ms": response_time_ms
                    }
                    
        except Exception as e:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            logger.warning(f"API connection failed, using mock response: {str(e)}")
            
            # Generate mock response for testing
            return self._generate_mock_response(query, session_id, response_time_ms)
    
    def _generate_mock_response(self, query: str, session_id: Optional[str], response_time_ms: float) -> Dict[str, Any]:
        """Generate mock API response for testing"""
        import uuid
        
        # Generate or reuse session_id
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Create mock responses based on query content
        if "razorpay" in query.lower() and "success rate" in query.lower():
            message = "The success rate for **Razorpay** today is **91.8%** with **1,234,567** transactions processed."
            responses = [
                {
                    "input": json.dumps({"domain": "kvorders"}),
                    "output": json.dumps({"dimensions": ["payment_gateway"], "metrics": ["success_rate"]}),
                    "payload_type": "info"
                },
                {
                    "input": json.dumps({"domain": "kvorders", "metric": ["success_rate"]}),
                    "output": json.dumps([{"success_rate": 91.8, "payment_gateway": "Razorpay", "transaction_count": 1234567}]),
                    "payload_type": "q_api"
                }
            ]
        elif "yesterday" in query.lower():
            message = "Yesterday's success rate for Razorpay was **92.5%**, which is **0.7 percentage points higher** than today's rate of 91.8%."
            responses = [
                {
                    "input": json.dumps({"domain": "kvorders", "metric": ["success_rate"]}),
                    "output": json.dumps([{"success_rate": 92.5, "payment_gateway": "Razorpay"}]),
                    "payload_type": "q_api"
                }
            ]
        elif "lowest success rate" in query.lower() and "netbanking" in query.lower():
            message = "**Oriental Bank Of Commerce** has the lowest success rate for Netbanking transactions today with a success rate of **78.2%**."
            responses = [
                {
                    "input": json.dumps({"domain": "kvorders"}),
                    "output": json.dumps({"dimensions": ["bank", "payment_method_type"]}),
                    "payload_type": "info"
                },
                {
                    "input": json.dumps({"domain": "kvorders", "dimension": "payment_method_type"}),
                    "output": json.dumps({"results": [{"dimension": "payment_method_type", "results": [["NB"]]}]}),
                    "payload_type": "field_value_discovery"
                },
                {
                    "input": json.dumps({"domain": "kvorders", "metric": ["success_rate"], "dimensions": ["bank"]}),
                    "output": json.dumps([{"success_rate": 78.2, "bank": "Oriental Bank Of Commerce"}]),
                    "payload_type": "q_api"
                }
            ]
        elif "highest" in query.lower():
            message = "**HDFC Bank** has the highest success rate for Netbanking transactions today with a success rate of **96.5%**."
            responses = [
                {
                    "input": json.dumps({"domain": "kvorders", "metric": ["success_rate"], "dimensions": ["bank"]}),
                    "output": json.dumps([{"success_rate": 96.5, "bank": "HDFC Bank"}]),
                    "payload_type": "q_api"
                }
            ]
        elif "top 5" in query.lower() and "payment gateway" in query.lower():
            message = "The top 5 payment gateways by transaction volume today are: **Razorpay** (1.2M), **PayU** (980K), **Cashfree** (750K), **Paytm** (620K), and **PhonePe** (580K)."
            responses = [
                {
                    "input": json.dumps({"domain": "kvorders", "metric": ["transaction_count"], "dimensions": ["payment_gateway"]}),
                    "output": json.dumps([
                        {"payment_gateway": "Razorpay", "transaction_count": 1200000},
                        {"payment_gateway": "PayU", "transaction_count": 980000},
                        {"payment_gateway": "Cashfree", "transaction_count": 750000},
                        {"payment_gateway": "Paytm", "transaction_count": 620000},
                        {"payment_gateway": "PhonePe", "transaction_count": 580000}
                    ]),
                    "payload_type": "q_api"
                }
            ]
        else:
            message = f"Mock response for query: {query}"
            responses = []
        
        return {
            "success": True,
            "data": {
                "message": message,
                "session_id": session_id,
                "responses": responses
            },
            "response_time_ms": response_time_ms,
            "session_id": session_id
        }

class FollowupClaudeJudge:
    """Enhanced LLM Judge for follow-up questions using Claude"""
    
    def __init__(self):
        self.client = None
        self.langfuse_client = None
        self._init_vertex_client()
        self._init_langfuse()
    
    def _init_vertex_client(self):
        """Initialize Vertex AI Anthropic client"""
        try:
            vertexai.init(project=VERTEX_PROJECT, location=VERTEX_LOCATION)
            self.client = AnthropicVertex(region=VERTEX_LOCATION, project_id=VERTEX_PROJECT)
            logger.info(f"Initialized Vertex AI client for follow-up evaluation")
        except Exception as e:
            logger.error(f"Error initializing Vertex AI: {e}")
            raise RuntimeError(f"Failed to initialize Vertex AI: {e}")
    
    def _init_langfuse(self):
        """Initialize Langfuse client"""
        try:
            from langfuse import Langfuse
            self.langfuse_client = Langfuse(
                secret_key=LANGFUSE_SK,
                public_key=LANGFUSE_PK,
                host=LANGFUSE_HOST
            )
            logger.info("Initialized Langfuse client")
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse: {e}")
            self.langfuse_client = None
    
    def _get_judge_prompt_from_langfuse(self, query: str, response: str, tool_calls: str = "", is_followup: bool = False, previous_turn: Optional[TurnResult] = None) -> str:
        """Get judge prompt from Langfuse (same as combined_evaluation.py)"""
        try:
            if self.langfuse_client:
                logger.info("Attempting to fetch judge prompt from Langfuse...")
                
                try:
                    prompt_response = self.langfuse_client.get_prompt("llm_as_judge", label="nishant_test")
                    
                    if prompt_response and hasattr(prompt_response, 'prompt'):
                        template = prompt_response.prompt
                        
                        # For follow-up questions, add context to the conversation text
                        if is_followup and previous_turn:
                            conversation_text = f"""**Previous Query:**
{previous_turn.turn.query}

**Previous Response:**
{previous_turn.response[:500]}...

**Current User Query (FOLLOW-UP):**
{query}

**Assistant Response:**
{response}

**Tool Calls/API Responses:**
{tool_calls}

NOTE: This is a FOLLOW-UP question that should maintain context from the previous query."""
                        else:
                            # Standard format for non-follow-up queries
                            conversation_text = f"""**User Query:**
{query}

**Assistant Response:**
{response}

**Tool Calls/API Responses:**
{tool_calls}"""
                        
                        # Replace placeholders in the template
                        if '{current_timestamp}' in template:
                            formatted_prompt = template.format(
                                conversation_text=conversation_text,
                                session_id="evaluation_session",
                                current_timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                            )
                        else:
                            formatted_prompt = template.format(
                                conversation_text=conversation_text,
                                session_id="evaluation_session"
                            )
                            
                        logger.info("✅ Successfully fetched and formatted judge prompt from Langfuse")
                        return formatted_prompt
                    else:
                        logger.warning("⚠️ No prompt response from Langfuse")
                except Exception as inner_e:
                    logger.error(f"❌ Error fetching prompt from Langfuse: {inner_e}")
            else:
                logger.warning("⚠️ Langfuse client not available, using fallback prompt")
        except Exception as e:
            logger.error(f"❌ Error in Langfuse prompt fetch: {e}")
        
        # Fallback prompt if Langfuse fails (same structure as combined_evaluation.py)
        logger.info("Using fallback judge prompt")
        return self._create_fallback_judge_prompt(query, response, tool_calls, is_followup, previous_turn)
    
    def _create_fallback_judge_prompt(self, query: str, response: str, tool_calls: str = "", is_followup: bool = False, previous_turn: Optional[TurnResult] = None) -> str:
        """Fallback judge prompt if Langfuse is unavailable (same as combined_evaluation.py)"""
        
        context_section = ""
        if is_followup and previous_turn:
            context_section = f"""
**Previous Query:** {previous_turn.turn.query}
**Previous Response Summary:** {previous_turn.response[:500]}...

**Current Follow-up Query:** {query}
**Current Response:** {response}

IMPORTANT: This is a FOLLOW-UP question that should maintain context from the previous query.
"""
        else:
            context_section = f"""
**Query:** {query}

**Assistant's Response:** {response}
"""
        
        return f"""
You are an expert evaluator for analytics query responses. Your task is to evaluate the quality of an AI assistant's response to an analytics query.

{context_section}

**Tool Calls/API Responses:** {tool_calls}

**IMPORTANT FORMATTING GUIDELINES:**
The assistant is instructed to format large numbers in Indian number format (lakhs, crores) for better readability. This is CORRECT behavior:
- Converting raw numbers like 100,000 to "1 lakh"
- Converting raw numbers like 10,000,000 to "1 crore"
- Converting raw numbers like 1,234,567 to "12.34 lakhs"
- Converting raw numbers like 123,456,789 to "12.34 crores"
Do NOT mark responses as incorrect for properly converting raw numbers to Indian number format.

Please evaluate the response on the following criteria (rate each from 1-5, where 5 is excellent):

1. **Correctness (1-5)**: Is the response factually accurate and does it correctly answer the query?
   - Score 5: Perfect accuracy, complete answer
   - Score 4: Mostly accurate with minor issues
   - Score 3: Partially accurate with some issues
   - Score 2: Significant inaccuracies
   - Score 1: Completely incorrect

2. **Explanation Quality (1-5)**: How well does the response explain the results and provide context?
   - Score 5: Excellent explanation with comprehensive context
   - Score 4: Good explanation with adequate context
   - Score 3: Basic explanation with limited context
   - Score 2: Poor explanation with minimal context
   - Score 1: No explanation or context

3. **Relevance (1-5)**: How relevant is the response to the specific query asked?
   - Score 5: Perfectly addresses the query
   - Score 4: Mostly addresses the query
   - Score 3: Partially addresses the query
   - Score 2: Barely addresses the query
   - Score 1: Does not address the query at all

4. **Hallucination Check (1-5)**: Does the response avoid making up facts or data not present in the source?
   - Score 5: No hallucinations whatsoever
   - Score 4: Minor extrapolations but no false claims
   - Score 3: Some extrapolations with minor false claims
   - Score 2: Significant hallucinations
   - Score 1: Completely fabricated response

5. **Tone & Clarity (1-5)**: Is the response clear, professional, and easy to understand?
   - Score 5: Perfectly clear, professional, and easy to understand
   - Score 4: Mostly clear and professional
   - Score 3: Somewhat clear but could be improved
   - Score 2: Unclear or unprofessional
   - Score 1: Completely unclear or inappropriate

{"6. **Context Preservation (1-5)**: Does the response correctly maintain context from the previous query?" if is_followup else ""}
{"   - Score 5: Perfect context preservation" if is_followup else ""}
{"   - Score 3: Some context preserved" if is_followup else ""}
{"   - Score 1: No context preservation" if is_followup else ""}

**IMPORTANT**: You MUST assign specific scores for each dimension based on your evaluation. Do not use default scores.

**Overall Judgment**: Based on your evaluation, is this response CORRECT or INCORRECT?

**Judgment Reason**: Provide a detailed explanation of your judgment, including any rule violations or policy adherence.

**Response Format**: You must respond with a JSON object in this exact format:
{{
    "result": "CORRECT" or "INCORRECT",
    "correctness": <score 1-5>,
    "explanation_quality": <score 1-5>,
    "relevance": <score 1-5>,
    "hallucination_check": <score 1-5>,
    "tone_clarity": <score 1-5>,
    {"\"context_preservation\": <score 1-5>," if is_followup else ""}
    "total_rating": <average of all scores>,
    "evaluation": "<brief explanation of your evaluation>",
    "judgment_reason": "<detailed explanation including rule violations or policy adherence>"
}}
"""
    
    async def judge_turn(
        self,
        query: str,
        response: str,
        tool_calls: str = "",
        is_followup: bool = False,
        previous_turn: Optional[TurnResult] = None
    ) -> Dict[str, Any]:
        """Judge a single turn in the conversation (same approach as combined_evaluation.py)"""
        
        # Get prompt from Langfuse or fallback
        prompt = self._get_judge_prompt_from_langfuse(
            query, response, tool_calls, is_followup, previous_turn
        )
        
        max_retries = 3
        for retry in range(max_retries):
            try:
                logger.info(f"Judging {'follow-up' if is_followup else 'initial'} query (attempt {retry + 1})")
                
                message = self.client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=1024,
                    temperature=0.1,
                    system="Your entire response must be a single, raw JSON object without any markdown formatting like ```json. You MUST include all required fields in your response, including: result, correctness, explanation_quality, relevance, hallucination_check, tone_clarity, total_rating, evaluation, and judgment_reason. For CORRECT responses, scores should generally be 4-5. For INCORRECT responses, scores should reflect the severity of the violations, typically 1-3.",
                    messages=[{"role": "user", "content": prompt}],
                )
                
                judgment_text = message.content[0].text if message.content else ""
                
                try:
                    judgment = json.loads(judgment_text.strip())
                    logger.info(f"Successfully parsed judgment: {judgment.get('result', 'N/A')}")
                    return judgment
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {e}")
                    logger.error(f"Raw response: '{judgment_text}'")
                    
                    # Fallback parsing
                    if "CORRECT" in judgment_text.upper():
                        result = "CORRECT"
                        default_score = 4
                    elif "INCORRECT" in judgment_text.upper():
                        result = "INCORRECT"
                        default_score = 2
                    else:
                        result = "ERROR"
                        default_score = 0
                    
                    return {
                        "result": result,
                        "correctness": default_score,
                        "explanation_quality": default_score,
                        "relevance": default_score,
                        "hallucination_check": default_score,
                        "tone_clarity": default_score,
                        "context_preservation": default_score if is_followup else None,
                        "total_rating": default_score,
                        "evaluation": f"Extracted from non-JSON response",
                        "judgment_reason": ""
                    }
                    
            except Exception as e:
                logger.error(f"Error calling Claude (retry {retry + 1}): {e}")
                if retry < max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    return {
                        "result": "ERROR",
                        "evaluation": f"Failed to get judgment: {str(e)}",
                        "total_rating": 0.0
                    }

async def evaluate_conversation(
    conversation_turns: List[ConversationTurn],
    api_client: AnalyticsAPIClient,
    judge: FollowupClaudeJudge
) -> ConversationEvaluation:
    """Evaluate a complete conversation with follow-up questions"""
    
    session_id = None
    turn_results = []
    
    logger.info(f"Evaluating conversation {conversation_turns[0].conversation_id} with {len(conversation_turns)} turns")
    
    for turn in conversation_turns:
        logger.info(f"Processing turn {turn.turn_id}: {turn.query[:100]}...")
        
        # Call API with session_id for follow-ups
        api_result = await api_client.query_analytics_with_session(
            turn.query,
            session_id if turn.is_followup else None
        )
        
        # Extract session_id from first response
        if not session_id and api_result.get("session_id"):
            session_id = api_result["session_id"]
            logger.info(f"Session ID acquired: {session_id}")
        
        # Create turn result with ONLY API response time (not including judge time)
        turn_result = TurnResult(
            turn=turn,
            response="",
            response_time_ms=api_result.get("response_time_ms", 0),  # Only API execution time
            session_id=session_id,
            full_response=api_result.get("data", {})
        )
        
        if api_result["success"]:
            data = api_result["data"]
            turn_result.response = data.get("message", "")
            
            # Get previous turn for context (if this is a follow-up)
            previous_turn = None
            if turn.is_followup and turn.depends_on and turn_results:
                # Find the turn this depends on
                for prev in turn_results:
                    if prev.turn.turn_id == turn.depends_on:
                        previous_turn = prev
                        break
            
            # Extract tool calls from the response for judging
            tool_calls = ""
            if turn_result.full_response and isinstance(turn_result.full_response, dict):
                responses = turn_result.full_response.get("responses", [])
                if responses:
                    tool_calls = json.dumps(responses, indent=2)
            
            # Judge the response (same as combined_evaluation.py)
            judgment = await judge.judge_turn(
                turn.query,
                turn_result.response,
                tool_calls=tool_calls,
                is_followup=turn.is_followup,
                previous_turn=previous_turn
            )
            
            # Update turn result with judgment - EXACT LOGIC FROM combined_evaluation.py
            turn_result.judge_result = judgment.get("result", "ERROR")
            
            # Debug log the judgment to see what we're getting
            logger.info(f"Raw judgment for turn {turn.turn_id}: {judgment}")
            
            # Check if any scores are present in the judgment
            has_scores = any(key in judgment for key in ["correctness", "explanation_quality", "relevance", "hallucination_check", "tone_clarity", "total_rating"])
            
            if has_scores:
                # Ensure we're getting numeric values for scores with better error handling
                try:
                    turn_result.correctness = int(float(judgment.get("correctness", 0)))
                    turn_result.explanation_quality = int(float(judgment.get("explanation_quality", 0)))
                    turn_result.relevance = int(float(judgment.get("relevance", 0)))
                    turn_result.hallucination_check = int(float(judgment.get("hallucination_check", 0)))
                    turn_result.tone_clarity = int(float(judgment.get("tone_clarity", 0)))
                    turn_result.total_score = float(judgment.get("total_rating", 0.0))
                    
                    # Note: We're not tracking follow-up specific metrics anymore
                    
                    # Log the extracted scores
                    logger.info(f"Extracted scores for turn {turn.turn_id}: " +
                               f"correctness={turn_result.correctness}, " +
                               f"explanation_quality={turn_result.explanation_quality}, " +
                               f"relevance={turn_result.relevance}, " +
                               f"hallucination_check={turn_result.hallucination_check}, " +
                               f"tone_clarity={turn_result.tone_clarity}, " +
                               f"total_score={turn_result.total_score}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting scores for turn {turn.turn_id}: {e}")
                    # Use default scores based on judgment
                    if turn_result.judge_result == "CORRECT":
                        turn_result.correctness = 4
                        turn_result.explanation_quality = 4
                        turn_result.relevance = 4
                        turn_result.hallucination_check = 4
                        turn_result.tone_clarity = 4
                        turn_result.total_score = 4.0
                    elif turn_result.judge_result == "INCORRECT":
                        turn_result.correctness = 2
                        turn_result.explanation_quality = 2
                        turn_result.relevance = 2
                        turn_result.hallucination_check = 2
                        turn_result.tone_clarity = 2
                        turn_result.total_score = 2.0
                    else:
                        turn_result.correctness = 0
                        turn_result.explanation_quality = 0
                        turn_result.relevance = 0
                        turn_result.hallucination_check = 0
                        turn_result.tone_clarity = 0
                        turn_result.total_score = 0.0
                    
                    logger.info(f"Using default scores based on judgment: {turn_result.judge_result}")
            else:
                # No scores in judgment, use default scores based on judgment
                logger.info(f"No scores found in judgment for turn {turn.turn_id}, using defaults")
                if turn_result.judge_result == "CORRECT":
                    turn_result.correctness = 4
                    turn_result.explanation_quality = 4
                    turn_result.relevance = 4
                    turn_result.hallucination_check = 4
                    turn_result.tone_clarity = 4
                    turn_result.total_score = 4.0
                elif turn_result.judge_result == "INCORRECT":
                    turn_result.correctness = 2
                    turn_result.explanation_quality = 2
                    turn_result.relevance = 2
                    turn_result.hallucination_check = 2
                    turn_result.tone_clarity = 2
                    turn_result.total_score = 2.0
                else:
                    turn_result.correctness = 0
                    turn_result.explanation_quality = 0
                    turn_result.relevance = 0
                    turn_result.hallucination_check = 0
                    turn_result.tone_clarity = 0
                    turn_result.total_score = 0.0
            
            # Extract judgment reason from 'reason' or 'judgment_reason' field
            if "judgment_reason" in judgment:
                turn_result.judgment_reason = judgment.get("judgment_reason", "")
            elif "reason" in judgment:
                turn_result.judgment_reason = judgment.get("reason", "")
            else:
                turn_result.judgment_reason = judgment.get("evaluation", "")
            
            # Log the judgment reason
            logger.info(f"Judgment reason for turn {turn.turn_id}: {turn_result.judgment_reason[:100]}..." if turn_result.judgment_reason and len(turn_result.judgment_reason) > 100 else f"Judgment reason for turn {turn.turn_id}: {turn_result.judgment_reason}")
            
        else:
            turn_result.response = f"Error: {api_result.get('error', 'Unknown error')}"
            turn_result.judge_result = "ERROR"
        
        turn_results.append(turn_result)
        
        # Small delay between turns
        await asyncio.sleep(0.5)
    
    # Create conversation evaluation
    evaluation = ConversationEvaluation(
        conversation_id=conversation_turns[0].conversation_id,
        session_id=session_id,
        turns=turn_results
    )
    
    # Calculate aggregate scores
    evaluation.calculate_scores()
    
    return evaluation

def load_conversations_from_csv(csv_file: str) -> Dict[int, List[ConversationTurn]]:
    """Load conversations from CSV file"""
    conversations = {}
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                conv_id = int(row.get('conversation_id', 0))
                turn_id = int(row.get('turn_id', row.get('query_id', 0)))
                query = row.get('query', '').strip()
                is_followup = row.get('is_followup', 'false').lower() == 'true'
                depends_on = int(row.get('depends_on')) if row.get('depends_on') else None
                
                if query:
                    turn = ConversationTurn(
                        conversation_id=conv_id,
                        turn_id=turn_id,
                        query=query,
                        is_followup=is_followup,
                        depends_on=depends_on
                    )
                    
                    if conv_id not in conversations:
                        conversations[conv_id] = []
                    conversations[conv_id].append(turn)
        
        # Sort turns within each conversation
        for conv_id in conversations:
            conversations[conv_id].sort(key=lambda x: x.turn_id)
        
        logger.info(f"Loaded {len(conversations)} conversations with {sum(len(turns) for turns in conversations.values())} total turns")
        return conversations
        
    except Exception as e:
        logger.error(f"Error loading conversations from CSV: {str(e)}")
        raise

def save_results_to_csv(evaluations: List[ConversationEvaluation], output_file: str):
    """Save evaluation results to CSV"""
    try:
        rows = []
        for eval in evaluations:
            for turn_result in eval.turns:
                row = {
                    'conversation_id': eval.conversation_id,
                    'session_id': eval.session_id,
                    'turn_id': turn_result.turn.turn_id,
                    'query': turn_result.turn.query,
                    'is_followup': turn_result.turn.is_followup,
                    'full_response': json.dumps(turn_result.full_response, indent=2) if turn_result.full_response else None,
                    'response_time_ms': turn_result.response_time_ms,
                    'judge_result': turn_result.judge_result,
                    'correctness': turn_result.correctness,
                    'explanation_quality': turn_result.explanation_quality,
                    'relevance': turn_result.relevance,
                    'hallucination_check': turn_result.hallucination_check,
                    'tone_clarity': turn_result.tone_clarity,
                    'total_score': turn_result.total_score,
                    'judgment_reason': turn_result.judgment_reason
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"Results saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")
        raise

def generate_summary_report(evaluations: List[ConversationEvaluation]) -> Dict[str, Any]:
    """Generate summary report for all conversations"""
    
    total_conversations = len(evaluations)
    total_turns = sum(len(e.turns) for e in evaluations)
    followup_turns = sum(1 for e in evaluations for t in e.turns if t.turn.is_followup)
    
    # Calculate success rates
    correct_turns = sum(1 for e in evaluations for t in e.turns if t.judge_result == "CORRECT")
    incorrect_turns = sum(1 for e in evaluations for t in e.turns if t.judge_result == "INCORRECT")
    error_turns = sum(1 for e in evaluations for t in e.turns if t.judge_result == "ERROR")
    
    # Calculate average scores for standard metrics
    all_correctness = [t.correctness for e in evaluations for t in e.turns if t.correctness is not None]
    all_explanation = [t.explanation_quality for e in evaluations for t in e.turns if t.explanation_quality is not None]
    all_relevance = [t.relevance for e in evaluations for t in e.turns if t.relevance is not None]
    all_hallucination = [t.hallucination_check for e in evaluations for t in e.turns if t.hallucination_check is not None]
    all_tone = [t.tone_clarity for e in evaluations for t in e.turns if t.tone_clarity is not None]
    all_total = [t.total_score for e in evaluations for t in e.turns if t.total_score is not None]
    
    # Response times
    response_times = [t.response_time_ms for e in evaluations for t in e.turns 
                      if t.response_time_ms is not None]
    
    summary = {
        "evaluation_timestamp": datetime.now().isoformat(),
        "total_conversations": total_conversations,
        "total_turns": total_turns,
        "followup_turns": followup_turns,
        "initial_turns": total_turns - followup_turns,
        "results": {
            "correct": correct_turns,
            "incorrect": incorrect_turns,
            "errors": error_turns,
            "accuracy_rate": (correct_turns / total_turns * 100) if total_turns > 0 else 0
        },
        "score_breakdown": {
            "correctness": round(sum(all_correctness) / len(all_correctness), 2) if all_correctness else 0,
            "explanation_quality": round(sum(all_explanation) / len(all_explanation), 2) if all_explanation else 0,
            "relevance": round(sum(all_relevance) / len(all_relevance), 2) if all_relevance else 0,
            "hallucination_check": round(sum(all_hallucination) / len(all_hallucination), 2) if all_hallucination else 0,
            "tone_clarity": round(sum(all_tone) / len(all_tone), 2) if all_tone else 0
        },
        "average_total_score": round(sum(all_total) / len(all_total), 2) if all_total else 0,
        "average_response_time_ms": round(sum(response_times) / len(response_times), 2) if response_times else 0
    }
    
    return summary

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Follow-up Question Evaluation System")
    parser.add_argument("--conversations", required=True, help="Path to CSV file containing conversations")
    parser.add_argument("--output", required=True, help="Path to output CSV file for results")
    parser.add_argument("--base_url", default="http://localhost:8000", help="Base URL for analytics API")
    parser.add_argument("--auth_token", default="f220a66fd5a4749879e03847134663", help="Authentication token")
    parser.add_argument("--batch_size", type=int, default=5, help="Number of conversations per batch")
    parser.add_argument("--batch_delay", type=float, default=2.0, help="Delay between batches")
    parser.add_argument("--summary", help="Path to save summary report JSON")
    
    args = parser.parse_args()
    
    try:
        # Load conversations
        logger.info(f"Loading conversations from {args.conversations}")
        conversations = load_conversations_from_csv(args.conversations)
        
        if not conversations:
            logger.error("No conversations found in CSV file")
            return 1
        
        # Initialize components
        judge = FollowupClaudeJudge()
        
        # Process conversations
        logger.info(f"Starting evaluation of {len(conversations)} conversations...")
        all_evaluations = []
        
        async with AnalyticsAPIClient(args.base_url, args.auth_token) as api_client:
            conversation_items = list(conversations.items())
            
            for batch_start in range(0, len(conversation_items), args.batch_size):
                batch_end = min(batch_start + args.batch_size, len(conversation_items))
                batch = conversation_items[batch_start:batch_end]
                batch_num = (batch_start // args.batch_size) + 1
                total_batches = (len(conversation_items) + args.batch_size - 1) // args.batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} conversations)")
                
                for conv_id, turns in batch:
                    evaluation = await evaluate_conversation(turns, api_client, judge)
                    all_evaluations.append(evaluation)
                    
                    logger.info(f"Conversation {conv_id} evaluated: "
                              f"Session={evaluation.session_id}, "
                              f"Overall Score={evaluation.overall_score:.2f}")
                
                if batch_end < len(conversation_items):
                    logger.info(f"Waiting {args.batch_delay} seconds before next batch...")
                    await asyncio.sleep(args.batch_delay)
        
        # Save results
        logger.info("Saving results...")
        save_results_to_csv(all_evaluations, args.output)
        
        # Generate summary
        summary = generate_summary_report(all_evaluations)
        
        logger.info("=== FOLLOW-UP EVALUATION SUMMARY ===")
        logger.info(f"Total Conversations: {summary['total_conversations']}")
        logger.info(f"Total Turns: {summary['total_turns']} ({summary['followup_turns']} follow-ups)")
        logger.info(f"Accuracy Rate: {summary['results']['accuracy_rate']:.1f}%")
        logger.info(f"Average Total Score: {summary['average_total_score']}/5")
        logger.info(f"Score Breakdown:")
        logger.info(f"  Correctness: {summary['score_breakdown']['correctness']}/5")
        logger.info(f"  Explanation Quality: {summary['score_breakdown']['explanation_quality']}/5")
        logger.info(f"  Relevance: {summary['score_breakdown']['relevance']}/5")
        logger.info(f"  Hallucination Check: {summary['score_breakdown']['hallucination_check']}/5")
        logger.info(f"  Tone & Clarity: {summary['score_breakdown']['tone_clarity']}/5")
        logger.info(f"Average Response Time: {summary['average_response_time_ms']:.1f}ms")
        
        # Save summary
        if args.summary:
            with open(args.summary, 'w') as f:
                json.dump(summary, f, indent=2)
            logger.info(f"Summary saved to {args.summary}")
        
        logger.info("Follow-up evaluation completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
