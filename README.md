# Cardano Wallet Health & Risk Scoring Agent

**A Masumi Network Service**

AI-powered Cardano wallet risk assessment available on the [Masumi Network](https://www.masumi.network) and [Sokosumi Marketplace](https://www.sokosumi.com).

## 🌐 How to Access

### Via Sokosumi Marketplace (Recommended)
The easiest way to use this service:
- **Find it on**: https://www.sokosumi.com
- **Price**: 0.05 ADA per wallet analysis
- **Payment**: Automatic via Masumi

### Via Masumi Network (Agent-to-Agent)
For AI agents and developers:
- **Service URL**: https://cardano-wallet-agent-production.up.railway.app
- **API Docs**: https://cardano-wallet-agent-production.up.railway.app/docs
- **MIP-003 Compliant**: Full A2A integration

**Note**: All requests require payment through the Masumi Payment Service.

## Features

- ✅ **AI-Powered Analysis**: OpenAI GPT-4o-mini for intelligent risk assessment
- ✅ **Multi-Perspective**: Security, DeFi, Behavioral, Compliance analysis
- ✅ **Real-Time Data**: Blockfrost integration for on-chain data
- ✅ **MIP-003 Compliant**: Full Masumi Network compatibility
- ✅ **Fast & Cached**: Instant results for repeated queries
- ✅ **Reliable**: 99%+ uptime on Railway infrastructure

## What You Get

### Comprehensive Risk Assessment
Analyzes Cardano wallets from 4 perspectives:
- **Security Risk**: Suspicious patterns, malicious actors
- **DeFi Risk**: Leverage, protocol vulnerabilities
- **Behavioral Risk**: Transaction velocity, counterparty diversity
- **Compliance Risk**: Mixing services, sanctioned entities

### Detailed Output
```json
{
  "risk_score": 23,
  "health": "safe",
  "reasons": [
    "Wallet demonstrates stable staking behavior for 682 days",
    "High counterparty diversity (0.72) suggests healthy ecosystem participation",
    "Known label 'exchange' adds credibility"
  ],
  "balances": {
    "ada": 1543.21,
    "token_count": 3
  },
  "staking": {
    "delegated": true,
    "pool_id": "pool1xyz"
  }
}
```

See more examples in the `/examples` folder.

## Use Cases

### For Individuals
- Check wallet safety before sending ADA
- Assess counterparty risk before trading
- Review your own wallet health

### For DeFi Protocols
- Assess borrower risk before approving loans
- Flag high-risk wallets for compliance
- Evaluate delegator wallet quality

### For Businesses
- KYC/AML wallet screening
- Transaction risk assessment
- Regulatory reporting

### For AI Agents
- Automated risk checks in multi-agent workflows
- Decision support for financial operations
- Integration with other Masumi services

## Documentation

- **[Agent Overview](docs/AGENT_OVERVIEW.md)** - Detailed service description
- **[Terms of Use](docs/TERMS_OF_USE.md)** - Legal terms
- **[Privacy Policy](docs/PRIVACY_POLICY.md)** - Privacy policy
- **[Support](docs/SUPPORT.md)** - Get help

## Support

- **Email**: kfagermo@gmail.com
- **Issues**: https://github.com/Kfagermo/cardano-wallet-agent/issues
- **Documentation**: See `/docs` folder

## About

This service is built and maintained for the Masumi Network ecosystem. It provides professional-grade wallet risk assessment using AI and real-time blockchain data.

**Masumi Network**: https://www.masumi.network  
**Sokosumi Marketplace**: https://www.sokosumi.com

---

© 2025 Cardano Wallet Health & Risk Scoring Agent. All rights reserved.
