# CAIS Proxy-Fitness Evidence Packet

- Anchor: `OpenBB-finance-OpenBB`
- Candidate: `quantsbin/Quantsbin`
- Repository URL: https://github.com/quantsbin/Quantsbin

## Repository metadata

Description: Quantitative Finance tools

Topics: python, finance, quants, quantitative-finance, derivatives, derivative-pricing, option-pricing, options, blackscholes, binomial-tree, monte-carlo-simulation, monte-carlo-methods

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

[![PyPi version](https://img.shields.io/pypi/v/quantsbin.svg?maxAge=60)](https://pypi.python.org/pypi/pandas-montecarlo) [![PyPi Status](https://img.shields.io/pypi/status/quantsbin.svg?maxAge=60)](https://pypi.python.org/pypi/quantsbin) [![Github Stars](https://img.shields.io/github/stars/quantsbin/Quantsbin.svg?style=social&label=Star&maxAge=60)](https://github.com/quantsbin/Quantsbin) [![Twitter follows](https://img.shields.io/twitter/follow/quantsbin.svg?style=social&label=Follow%20Me&maxAge=60)](https://twitter.com/quantsbin) 

# Quantsbin

Open source library for finance.

Quantsbin 1.0.3, which started as a weekend project is currently in its initial phase and
incorporates tools for pricing and plotting of vanilla option prices, greeks and various other analysis around them.
We are working on optimising calculations and expanding the scope of library in multiple directions for future releases.

## Quantsbin 1.0.3 includes
   1. Option payoff, premium and greeks calculation for vanilla options on Equity, FX, Commodity and Futures.
   2. Capability to calculate greeks numerically for all models and also analytically for Black Scholes Model.
   3. Price vanilla options with European expiry using BSM, Binomial tree and MonteCarlo with option to 
      incorporate continuous compounded dividend yield for Equity options,
      cost and convenience yield for Commodity options and
      local and foreign risk-free rate in case of FX options.
      It also allows option to give discrete dividends in cased of Equity options.
   4. Price vanilla options with American expiry using Binomial tree and MonteCarlo(Longstaff Schwartz) method.
      There is option to provide discrete dividends for Equity options for both the models.
   5. Implied volatility calculation under BSM framework model.
   6. Option to create user defined or standard strategies using multiple single underlying options and
      directly generate and plot valuation and greeks for these strategies.

## License
[MIT LICENCE](https://github.com/quantsbin/Quantsbin/blob/master/LICENSE/)

## Dependencies and Installation details
      scipy==1.6.3
      pandas==1.2.4
      matplotlib==3.4.2
      numpy==1.18.0     
    
Install using setup.py:
```
>>> python setup.py install
```
Install using pip:
```
>>> pip install quantsbin
```

## Detailed documentation
Refer to our [Documentation](http://www.quantsbin.com/introduction-to-option-pricing-using-python-library-quantsbin/) page

## Our Website
For collaboration and suggestion reach us at [Quantsbin](http://www.quantsbin.com/)

## Tutorial
Refer to our [Tutorial](http://www.quantsbin.com/introduction-to-option-pricing-using-python-library-quantsbin/) page

## Note
For Quantsbin 1.0.3 documentation are still WIP.
