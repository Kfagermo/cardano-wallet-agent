"""
AI-Powered Wallet Analysis Service

This module provides intelligent wallet risk assessment using OpenAI API.
It analyzes on-chain data from multiple perspectives (security, DeFi, behavioral)
and generates nuanced risk scores with detailed reasoning.

Implements Masumi best practices for AI agent integration.
"""

import os
import json
from typing import Any, Dict, List, Tuple, Optional
from openai import AsyncOpenAI


class AIWalletAnalyzer:
    """
    AI-powered wallet analyzer using OpenAI GPT models.
    
    Analyzes wallet data from multiple perspectives:
    - Security risk (suspicious patterns, known bad actors)
    - DeFi risk (leverage, impermanent loss exposure)
    - Behavioral risk (transaction patterns, counterparty diversity)
    - Compliance risk (mixing services, sanctioned entities)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
    ):
        """
        Initialize AI analyzer.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use (gpt-4o-mini for cost efficiency)
            temperature: Sampling temperature (0.3 for consistent analysis)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set. Set via env var or constructor.")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = model
        self.temperature = temperature
    
    async def analyze_wallet(
        self,
        wallet_data: Dict[str, Any],
        network: str = "mainnet",
    ) -> Tuple[int, str, List[str]]:
        """
        Analyze wallet using AI reasoning.
        
        Args:
            wallet_data: On-chain data from Blockfrost (balances, staking, tx history)
            network: Cardano network (mainnet or preprod)
        
        Returns:
            Tuple of (risk_score, health_category, reasons)
            - risk_score: 0-100 (0=safest, 100=riskiest)
            - health_category: "safe", "caution", or "risky"
            - reasons: List of AI-generated insights
        """
        # Build analysis prompt with structured data
        prompt = self._build_analysis_prompt(wallet_data, network)
        
        # Call OpenAI API with structured output
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                response_format={"type": "json_object"},
            )
            
            # Parse AI response
            result = json.loads(response.choices[0].message.content)
            
            risk_score = int(result.get("risk_score", 50))
            health = result.get("health", "caution").lower()
            reasons = result.get("reasons", ["AI analysis completed"])
            
            # Validate and clamp
            risk_score = max(0, min(100, risk_score))
            if health not in ("safe", "caution", "risky"):
                health = "caution"
            
            return risk_score, health, reasons
            
        except Exception as e:
            # Fallback to deterministic analysis if AI fails
            return self._fallback_analysis(wallet_data)
    
    def _get_system_prompt(self) -> str:
        """System prompt defining the AI's role and analysis framework."""
        return """You are an expert Cardano blockchain analyst specializing in wallet risk assessment.

Your task is to analyze wallet on-chain data and provide a comprehensive risk evaluation from multiple perspectives:

1. **Security Risk**: Suspicious patterns, known malicious actors, phishing indicators
2. **DeFi Risk**: Leverage exposure, impermanent loss, protocol vulnerabilities
3. **Behavioral Risk**: Transaction velocity, counterparty diversity, age/maturity
4. **Compliance Risk**: Mixing services, sanctioned entities, high-risk jurisdictions

**Risk Score Scale (0-100)**:
- 0-33: Safe (low risk, stable patterns, good security practices)
- 34-66: Caution (moderate risk, some concerning patterns, needs monitoring)
- 67-100: Risky (high risk, suspicious activity, avoid interaction)

**Analysis Guidelines**:
- Consider context: New wallets aren't automatically risky
- Staking = positive signal (long-term commitment)
- High tx velocity can be legitimate (traders, businesses)
- Diverse counterparties = healthy ecosystem participation
- Known labels (exchanges, pools) reduce risk
- Low diversity + high velocity = potential bot/automation risk
- Very old wallets with no recent activity = dormant/abandoned

**Output Format** (JSON):
{
  "risk_score": <0-100>,
  "health": "<safe|caution|risky>",
  "reasons": [
    "<specific insight 1>",
    "<specific insight 2>",
    "<specific insight 3>"
  ],
  "perspectives": {
    "security": "<brief assessment>",
    "defi": "<brief assessment>",
    "behavioral": "<brief assessment>",
    "compliance": "<brief assessment>"
  }
}

Be specific and actionable in your reasoning. Avoid generic statements."""
    
    def _build_analysis_prompt(self, wallet_data: Dict[str, Any], network: str) -> str:
        """Build user prompt with wallet data."""
        return f"""Analyze this Cardano wallet on {network}:

**Balances**:
- ADA: {wallet_data.get('balances', {}).get('ada', 0)} ADA
- Tokens: {wallet_data.get('balances', {}).get('token_count', 0)} different tokens

**Staking**:
- Delegated: {wallet_data.get('staking', {}).get('delegated', False)}
- Pool: {wallet_data.get('staking', {}).get('pool_id', 'None')}
- Since: {wallet_data.get('staking', {}).get('since', 'N/A')}

**Activity**:
- First seen: {wallet_data.get('first_seen', 'Unknown')}
- Age: {wallet_data.get('age_days', 0)} days
- Transaction velocity (30d): {wallet_data.get('tx_velocity_30d', 0)} transactions
- Counterparty diversity (90d): {wallet_data.get('counterparty_diversity_90d', 0.0):.2f} (0=low, 1=high)

**Known Labels**: {wallet_data.get('known_label', 'None')}

**Top Tokens**:
{self._format_tokens(wallet_data.get('top_tokens', []))}

Provide a comprehensive risk assessment with specific, actionable insights."""
    
    def _format_tokens(self, tokens: List[Dict[str, Any]]) -> str:
        """Format token list for prompt."""
        if not tokens:
            return "None"
        
        lines = []
        for token in tokens[:5]:
            asset = token.get('asset', 'Unknown')[:20]
            qty = token.get('qty', '0')
            lines.append(f"  - {asset}: {qty}")
        
        return "\n".join(lines) if lines else "None"
    
    def _fallback_analysis(self, wallet_data: Dict[str, Any]) -> Tuple[int, str, List[str]]:
        """
        Fallback to deterministic analysis if AI fails.
        This is the original rule-based logic.
        """
        reasons: List[str] = []
        score = 50
        
        # Age and staking influence
        age_days = int(wallet_data.get("age_days", 0) or 0)
        if age_days >= 365:
            score -= 10
            reasons.append("address is older than 1 year (positive)")
        elif age_days < 30:
            score += 10
            reasons.append("new address (<30 days, needs monitoring)")
        
        # Staking
        staking = wallet_data.get("staking", {}) or {}
        if staking.get("delegated"):
            score -= 8
            reasons.append("delegated/staked ADA adds stability")
        
        # Velocity
        v30 = int(wallet_data.get("tx_velocity_30d", 0) or 0)
        if v30 > 100:
            score += 10
            reasons.append("very high recent tx velocity (potential bot)")
        elif v30 < 5:
            score -= 4
            reasons.append("low recent tx activity (dormant or holder)")
        
        # Diversity
        div = float(wallet_data.get("counterparty_diversity_90d", 0.0) or 0.0)
        if div >= 0.7:
            score -= 6
            reasons.append("diverse counterparties (healthy ecosystem participation)")
        elif div <= 0.2:
            score += 6
            reasons.append("low counterparty diversity (concentrated activity)")
        
        # Known label
        label = wallet_data.get("known_label")
        if label in ("exchange", "custody"):
            score -= 5
            reasons.append(f"known label: {label} (trusted entity)")
        
        # Clamp
        score = max(0, min(100, score))
        
        # Health bucket
        if score <= 33:
            health = "safe"
        elif score <= 66:
            health = "caution"
        else:
            health = "risky"
        
        if not reasons:
            reasons.append("no special risk factors identified (fallback analysis)")
        
        return score, health, reasons


class CrewAIWalletAnalyzer:
    """
    Multi-agent wallet analyzer using CrewAI framework.
    
    Deploys specialized agents for different analysis perspectives:
    - Security Analyst: Identifies threats and vulnerabilities
    - DeFi Analyst: Assesses protocol risks and exposure
    - Behavioral Analyst: Evaluates transaction patterns
    - Compliance Analyst: Checks regulatory concerns
    
    Agents collaborate to produce a comprehensive risk assessment.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize CrewAI analyzer.
        
        Args:
            openai_api_key: OpenAI API key for agent LLMs
        """
        try:
            from crewai import Agent, Task, Crew, Process
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "CrewAI not installed. Install with: pip install crewai langchain-openai"
            )
        
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY required for CrewAI")
        
        # Initialize LLM for agents
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=self.api_key,
        )
        
        # Store CrewAI classes
        self.Agent = Agent
        self.Task = Task
        self.Crew = Crew
        self.Process = Process
    
    async def analyze_wallet(
        self,
        wallet_data: Dict[str, Any],
        network: str = "mainnet",
    ) -> Tuple[int, str, List[str]]:
        """
        Analyze wallet using multi-agent CrewAI system.
        
        Args:
            wallet_data: On-chain data from Blockfrost
            network: Cardano network
        
        Returns:
            Tuple of (risk_score, health_category, reasons)
        """
        # Create specialized agents
        security_agent = self._create_security_agent()
        defi_agent = self._create_defi_agent()
        behavioral_agent = self._create_behavioral_agent()
        compliance_agent = self._create_compliance_agent()
        synthesizer_agent = self._create_synthesizer_agent()
        
        # Create analysis tasks
        wallet_summary = self._format_wallet_data(wallet_data, network)
        
        security_task = self.Task(
            description=f"Analyze security risks for this wallet:\n{wallet_summary}",
            agent=security_agent,
            expected_output="Security risk assessment with score 0-100 and key findings",
        )
        
        defi_task = self.Task(
            description=f"Analyze DeFi risks for this wallet:\n{wallet_summary}",
            agent=defi_agent,
            expected_output="DeFi risk assessment with score 0-100 and key findings",
        )
        
        behavioral_task = self.Task(
            description=f"Analyze behavioral patterns for this wallet:\n{wallet_summary}",
            agent=behavioral_agent,
            expected_output="Behavioral risk assessment with score 0-100 and key findings",
        )
        
        compliance_task = self.Task(
            description=f"Analyze compliance risks for this wallet:\n{wallet_summary}",
            agent=compliance_agent,
            expected_output="Compliance risk assessment with score 0-100 and key findings",
        )
        
        synthesis_task = self.Task(
            description="Synthesize all agent findings into a final risk assessment. Output JSON: {\"risk_score\": <0-100>, \"health\": \"<safe|caution|risky>\", \"reasons\": [\"<insight1>\", \"<insight2>\", ...]}",
            agent=synthesizer_agent,
            expected_output="Final JSON risk assessment",
            context=[security_task, defi_task, behavioral_task, compliance_task],
        )
        
        # Create crew and execute
        crew = self.Crew(
            agents=[security_agent, defi_agent, behavioral_agent, compliance_agent, synthesizer_agent],
            tasks=[security_task, defi_task, behavioral_task, compliance_task, synthesis_task],
            process=self.Process.sequential,
            verbose=False,
        )
        
        try:
            result = crew.kickoff()
            
            # Parse result (CrewAI returns string output from final task)
            result_str = str(result)
            
            # Try to extract JSON from result
            import re
            json_match = re.search(r'\{[^{}]*"risk_score"[^{}]*\}', result_str)
            if json_match:
                parsed = json.loads(json_match.group(0))
                risk_score = int(parsed.get("risk_score", 50))
                health = parsed.get("health", "caution").lower()
                reasons = parsed.get("reasons", ["Multi-agent analysis completed"])
            else:
                # Fallback parsing
                risk_score = 50
                health = "caution"
                reasons = [result_str[:200]]  # First 200 chars
            
            # Validate
            risk_score = max(0, min(100, risk_score))
            if health not in ("safe", "caution", "risky"):
                health = "caution"
            
            return risk_score, health, reasons
            
        except Exception as e:
            # Fallback to simple analysis
            return AIWalletAnalyzer(api_key=self.api_key)._fallback_analysis(wallet_data)
    
    def _create_security_agent(self) -> Any:
        """Create security analyst agent."""
        return self.Agent(
            role="Security Analyst",
            goal="Identify security threats, suspicious patterns, and vulnerabilities in wallet activity",
            backstory="Expert in blockchain security with 10+ years experience in threat detection and fraud prevention. Specializes in identifying phishing, scams, and malicious actors.",
            llm=self.llm,
            verbose=False,
        )
    
    def _create_defi_agent(self) -> Any:
        """Create DeFi analyst agent."""
        return self.Agent(
            role="DeFi Risk Analyst",
            goal="Assess DeFi protocol risks, leverage exposure, and impermanent loss potential",
            backstory="DeFi expert with deep knowledge of Cardano DEXs, lending protocols, and liquidity pools. Specializes in risk modeling and portfolio analysis.",
            llm=self.llm,
            verbose=False,
        )
    
    def _create_behavioral_agent(self) -> Any:
        """Create behavioral analyst agent."""
        return self.Agent(
            role="Behavioral Analyst",
            goal="Evaluate transaction patterns, counterparty relationships, and wallet maturity",
            backstory="Data scientist specializing in behavioral analytics and pattern recognition. Expert in identifying normal vs. anomalous wallet behavior.",
            llm=self.llm,
            verbose=False,
        )
    
    def _create_compliance_agent(self) -> Any:
        """Create compliance analyst agent."""
        return self.Agent(
            role="Compliance Analyst",
            goal="Check for regulatory concerns, sanctioned entities, and mixing service usage",
            backstory="Compliance officer with expertise in AML/KYC regulations and blockchain forensics. Specializes in identifying high-risk jurisdictions and entities.",
            llm=self.llm,
            verbose=False,
        )
    
    def _create_synthesizer_agent(self) -> Any:
        """Create synthesis agent to combine all findings."""
        return self.Agent(
            role="Risk Synthesis Manager",
            goal="Combine all analyst findings into a comprehensive, actionable risk assessment",
            backstory="Senior risk manager with 15+ years experience synthesizing complex analyses into clear recommendations. Expert in balancing multiple risk factors.",
            llm=self.llm,
            verbose=False,
        )
    
    def _format_wallet_data(self, wallet_data: Dict[str, Any], network: str) -> str:
        """Format wallet data for agent consumption."""
        return f"""
Network: {network}
ADA Balance: {wallet_data.get('balances', {}).get('ada', 0)}
Token Count: {wallet_data.get('balances', {}).get('token_count', 0)}
Staking: {wallet_data.get('staking', {}).get('delegated', False)}
Pool: {wallet_data.get('staking', {}).get('pool_id', 'None')}
Age: {wallet_data.get('age_days', 0)} days
First Seen: {wallet_data.get('first_seen', 'Unknown')}
Tx Velocity (30d): {wallet_data.get('tx_velocity_30d', 0)}
Counterparty Diversity (90d): {wallet_data.get('counterparty_diversity_90d', 0.0):.2f}
Known Label: {wallet_data.get('known_label', 'None')}
Top Tokens: {', '.join([t.get('asset', 'Unknown')[:20] for t in wallet_data.get('top_tokens', [])[:3]])}
"""


# Factory function for easy initialization
def create_analyzer(
    mode: str = "openai",
    api_key: Optional[str] = None,
) -> Any:
    """
    Create wallet analyzer based on mode.
    
    Args:
        mode: "openai" for single-agent AI, "crewai" for multi-agent system
        api_key: OpenAI API key (optional, uses env var if not provided)
    
    Returns:
        Analyzer instance (AIWalletAnalyzer or CrewAIWalletAnalyzer)
    """
    if mode == "crewai":
        return CrewAIWalletAnalyzer(openai_api_key=api_key)
    else:
        return AIWalletAnalyzer(api_key=api_key)
