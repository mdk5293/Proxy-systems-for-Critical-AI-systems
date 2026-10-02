# CAIS Proxy-Fitness Evidence Packet

- Anchor: `OpenBB-finance-OpenBB`
- Candidate: `binance/binance-skills-hub`
- Repository URL: https://github.com/binance/binance-skills-hub

## Repository metadata

Description: Binance Skills Hub is an open skills marketplace that gives AI agents native access to crypto

Topics: agents, ai, crypto, skills

## Frozen rubric

### OBB01 — Financial or market data ingestion

Critical: True

Supports acquisition of market, economic, company, asset, or comparable financial-domain data.

Score: 

Evidence source: 

Evidence note: 

### OBB02 — Financial analytics or time-series analysis

Critical: True

Supports analytical operations on financial, market, quantitative, or time-series information.

Score: 

Evidence source: 

Evidence note: 

### OBB03 — Multiple data-provider integration

Critical: False

Supports multiple providers, APIs, adapters, connectors, or interchangeable data sources.

Score: 

Evidence source: 

Evidence note: 

### OBB04 — Data provenance and reproducibility

Critical: False

Provides evidence of data source, parameters, timestamps, transformations, or other provenance needed to reproduce analysis.

Score: 

Evidence source: 

Evidence note: 

### OBB05 — Programmatic automation

Critical: False

Supports APIs, SDKs, scripts, pipelines, or automated analytical workflows.

Score: 

Evidence source: 

Evidence note: 

### OBB06 — Missing, delayed, or provider-error handling

Critical: False

Supports testing behavior when financial data are unavailable, incomplete, delayed, malformed, or provider access fails.

Score: 

Evidence source: 

Evidence note: 

## Retrieved README

# Binance Skills Hub

Binance Skills Hub is an open skills marketplace that gives AI agents native access to crypto: both centralized and decentralized. Search tokens, execute trades, track wallets, monitor signals, and interact with DeFi protocols, all through natural language.

Built by Binance. Built for everyone.

We're not building this just for Binance products. Skills Hub is designed for the entire crypto ecosystem: any agent, any framework, any chain. Whether you're building on LangChain, CrewAI, or your own stack, your agents can plug into crypto with a few lines of config.

---

## About This Repository

Each skill lives in its own folder and contains a `SKILL.md` file with YAML frontmatter and structured instructions.

Browse the existing skills to understand patterns and naming conventions before contributing.

---

## Installation

Get started with Binance Skills Hub in a single command. Works with various agents such as OpenClaw and Claude Code.

### Prerequisites

Before installing Binance Skills Hub, ensure you have the following prerequisites:

* **Node.js** (version 22 or higher)

### Install Skills Hub

Run the following command to add Binance Skills Hub to your project:

```bash
npx skills add https://github.com/binance/binance-skills-hub
```

### Authentication

For Binance Skills, certain endpoints require you to provide Binance API credentials. You can do this by setting environment variables, using a secrets file (such as `.env` or `.openclaw/secrets.env`) , or sending them directly to the agent in the chat. For more details, see the [Security](./skills/binance/spot/SKILL.md#security) section in each skill.

---

## Contribution

We welcome contributions.

To add a new skill:

1. **Fork the repository** and create a new branch:

   ```bash
   git checkout -b feature/<skill-name>
   ```

2. **Create a new folder** containing a `SKILL.md` file.

3. **Follow the required format:**

   ```markdown
   ---
   title: <Skill Name>
   description: A clear description of what the skill does and when to use it.
   metadata:
     version: <Skill Version>
     author: <Your Github Username>
   license: MIT
   ---

   # <Skill Name>

   [Add instructions, examples, and guidelines here]
   ```

4. **Open a Pull Request** to `main` for review.
   Once approved, the skill will be merged.

---

## Disclaimer

Binance Skills Hub is an informational tool only. Binance Skills Hub and its outputs are provided to you on an “as is” and “as available” basis, without representation or warranty of any kind. It does not constitute investment, financial, trading or any other form of advice; represent a recommendation to buy, sell or hold any assets; guarantee the accuracy, timeliness or completeness of the data or analysis presented. Your use of Binance Skills Hub and any information provided in connection with this feature is at your own risk, and you are solely responsible for evaluating the information provided and for all trading decisions made by you. Binance does not endorse or guarantee any AI-generated information. Any AI-generated information or summary should not be solely relied on for decision making. AI-generated content may include or reflect information, views and opinions of third parties, and may also include errors, biases or outdated information. Binance is not responsible for any losses or damages incurred as a result of your use of or reliance on the Binance Skills Hub feature. Binance may modify or discontinue the Binance Skills Hub feature at its discretion, and functionality may vary by region or user profile. Digital asset prices are subject to high market risk and price volatility. The value of your investment may go down or up, and you may not get back the amount invested. You are solely responsible for your investment decisions and Binance is not liable for any losses you may incur. Past performance is not a reliable predictor of future performance. You should only invest in products you are familiar with and where you understand the risks. You should carefully consider your investment experience, financial situation, investment objectives and risk tolerance and consult an independent financial adviser prior to making any investment. This material should not be construed as advice. For more information, please see our [Risk Warning](https://www.binance.com/en/risk-warning) and [Terms of Use](https://www.binance.com/en/terms).