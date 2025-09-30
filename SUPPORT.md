# Support & Contact

Welcome to the Cardano Wallet Health & Risk Scoring Agent support page!

## 📧 Contact Information

**Email**: kfagermo@gmail.com  
**GitHub**: https://github.com/Kfagermo/cardano-wallet-agent  
**Issues**: https://github.com/Kfagermo/cardano-wallet-agent/issues

---

## 🆘 Getting Help

### For Technical Issues
1. **Check the documentation**: See [README.md](README.md) for usage instructions
2. **Review API docs**: Visit https://cardano-wallet-agent-production.up.railway.app/docs
3. **Search existing issues**: https://github.com/Kfagermo/cardano-wallet-agent/issues
4. **Open a new issue**: If your problem isn't already reported

### For Billing/Payment Issues
- **Masumi Payment Service**: Contact Masumi support for payment-related questions
- **Refund requests**: See our [Terms of Use](TERMS_OF_USE.md) - all sales are final

### For General Inquiries
- **Email**: kfagermo@gmail.com
- **Response time**: Usually within 24-48 hours

---

## 📚 Documentation

### Quick Links
- **API Documentation**: https://cardano-wallet-agent-production.up.railway.app/docs
- **README**: [README.md](README.md)
- **Agent Overview**: [AGENT_OVERVIEW.md](AGENT_OVERVIEW.md)
- **Terms of Use**: [TERMS_OF_USE.md](TERMS_OF_USE.md)
- **Privacy Policy**: [PRIVACY_POLICY.md](PRIVACY_POLICY.md)

### Guides
- **Getting Started**: See [README.md](README.md#quick-start)
- **API Integration**: See [API Documentation](https://cardano-wallet-agent-production.up.railway.app/docs)
- **MIP-003 Compliance**: See [AGENT_OVERVIEW.md](AGENT_OVERVIEW.md#mip-003-compliance)

---

## 🐛 Reporting Bugs

Found a bug? Please report it!

### How to Report
1. Go to: https://github.com/Kfagermo/cardano-wallet-agent/issues
2. Click "New Issue"
3. Provide:
   - **Description**: What happened?
   - **Expected behavior**: What should have happened?
   - **Steps to reproduce**: How can we reproduce the issue?
   - **Environment**: Network (mainnet/preprod), timestamp, etc.
   - **Error messages**: Any error messages or logs

### Example Bug Report
```
Title: Risk score calculation returns NaN for address X

Description:
When analyzing address addr1qx..., the risk score returns NaN instead of a number.

Expected Behavior:
Should return a risk score between 0-100.

Steps to Reproduce:
1. Call /start_job with address addr1qx...
2. Check /status for job_id
3. Result shows "risk_score": NaN

Environment:
- Network: mainnet
- Timestamp: 2025-09-30 16:00:00 UTC
- Job ID: abc-123-def

Error Messages:
None visible in API response
```

---

## 💡 Feature Requests

Have an idea to improve the Service?

### How to Request
1. Go to: https://github.com/Kfagermo/cardano-wallet-agent/issues
2. Click "New Issue"
3. Label it as "enhancement"
4. Describe:
   - **Feature**: What do you want?
   - **Use case**: Why do you need it?
   - **Benefit**: How would it help?

---

## ❓ Frequently Asked Questions (FAQ)

### General Questions

**Q: How much does the Service cost?**  
A: 0.05 ADA per wallet address analysis.

**Q: What networks are supported?**  
A: Cardano mainnet and preprod testnet.

**Q: How long does analysis take?**  
A: Usually 1-3 seconds. Cached results are instant (<100ms).

**Q: Is my data private?**  
A: We only analyze public blockchain data. See our [Privacy Policy](PRIVACY_POLICY.md).

### Technical Questions

**Q: What is the API rate limit?**  
A: 60 requests per minute per IP address by default.

**Q: How do I integrate with my application?**  
A: See our [API Documentation](https://cardano-wallet-agent-production.up.railway.app/docs) for MIP-003 compliant endpoints.

**Q: Can I use this for agent-to-agent (A2A) integration?**  
A: Yes! The Service is fully MIP-003 compliant and registered on the Masumi Network.

**Q: What AI model do you use?**  
A: OpenAI GPT-4o-mini for cost-efficient, intelligent analysis.

### Payment Questions

**Q: How do I pay?**  
A: Payments are processed through the Masumi Payment Service using ADA.

**Q: Can I get a refund?**  
A: No, all payments are final. See [Terms of Use](TERMS_OF_USE.md).

**Q: Do you offer bulk discounts?**  
A: Contact us at kfagermo@gmail.com for bulk pricing inquiries.

### Analysis Questions

**Q: How accurate are the risk scores?**  
A: Risk scores are informational and based on AI analysis of public blockchain data. They are not financial advice. See [Terms of Use](TERMS_OF_USE.md).

**Q: What factors affect the risk score?**  
A: Age, transaction velocity, counterparty diversity, staking status, known labels, and more.

**Q: Can I dispute a risk score?**  
A: Risk scores are automated and informational. For specific concerns, contact us at kfagermo@gmail.com.

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: "Job not found" error
**Solution**: 
- Check that you're using the correct job_id
- Jobs may expire after 24 hours
- Ensure you're querying the correct network

#### Issue: "Payment timeout" error
**Solution**:
- Ensure payment was sent to the correct address
- Check payment status in Masumi Payment Service
- Contact Masumi support if payment was sent but not detected

#### Issue: "Invalid address" error
**Solution**:
- Verify the address format is correct
- Ensure you're using the correct network (mainnet vs preprod)
- Check for typos in the address

#### Issue: Slow response times
**Solution**:
- First request may take 1-3 seconds (AI analysis)
- Subsequent requests for the same address are cached (instant)
- Check your network connection

---

## 🚀 Service Status

**Current Status**: ✅ Operational

**Service URL**: https://cardano-wallet-agent-production.up.railway.app

**Check Status**:
```bash
curl https://cardano-wallet-agent-production.up.railway.app/availability
```

**Expected Response**:
```json
{"status":"available","uptime":1234567890,"message":"OK"}
```

---

## 📊 Performance & Uptime

**Target SLA**: 99% uptime  
**Average Response Time**: 1-3 seconds (AI analysis), <100ms (cached)  
**Rate Limit**: 60 requests/minute  
**Cache Duration**: 24 hours

---

## 🤝 Contributing

Interested in contributing to the project?

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
5. We'll review and merge if appropriate

---

## 📜 Legal

- **Terms of Use**: [TERMS_OF_USE.md](TERMS_OF_USE.md)
- **Privacy Policy**: [PRIVACY_POLICY.md](PRIVACY_POLICY.md)
- **License**: See [LICENSE](LICENSE) file

---

## 🌐 Community

- **Masumi Network**: https://www.masumi.network
- **Sokosumi Marketplace**: https://www.sokosumi.com
- **Masumi Discord**: https://discord.gg/masumi

---

## 📞 Contact Summary

| Type | Contact |
|------|---------|
| **General Support** | kfagermo@gmail.com |
| **Bug Reports** | https://github.com/Kfagermo/cardano-wallet-agent/issues |
| **Feature Requests** | https://github.com/Kfagermo/cardano-wallet-agent/issues |
| **API Documentation** | https://cardano-wallet-agent-production.up.railway.app/docs |
| **GitHub** | https://github.com/Kfagermo/cardano-wallet-agent |

---

**Thank you for using the Cardano Wallet Health & Risk Scoring Agent!** 🎉

We're here to help. Don't hesitate to reach out if you need assistance.
