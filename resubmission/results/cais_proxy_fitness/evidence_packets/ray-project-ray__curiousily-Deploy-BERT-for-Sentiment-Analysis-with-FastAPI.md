# CAIS Proxy-Fitness Evidence Packet

- Anchor: `ray-project-ray`
- Candidate: `curiousily/Deploy-BERT-for-Sentiment-Analysis-with-FastAPI`
- Repository URL: https://github.com/curiousily/Deploy-BERT-for-Sentiment-Analysis-with-FastAPI

## Repository metadata

Description: Deploy BERT for Sentiment Analysis as REST API using FastAPI, Transformers by Hugging Face and PyTorch

Topics: transformers, bert, huggingface-transformer, huggingface, pytorch, deployment, fastapi, python, machine-learning, deep-learning, deploy-machine-learning, sentiment-analysis, rest, rest-api, uvicorn

## Frozen rubric

### RAY01 — Distributed execution

Critical: True

Supports execution of work across multiple workers, processes, nodes, or distributed resources.

Score: 

Evidence source: 

Evidence note: 

### RAY02 — Fault tolerance and recovery

Critical: True

Supports worker, process, task, node, or job failure handling and recovery.

Score: 

Evidence source: 

Evidence note: 

### RAY03 — Distributed model training

Critical: False

Supports scalable or distributed model-training workloads.

Score: 

Evidence source: 

Evidence note: 

### RAY04 — Model inference or serving

Critical: False

Supports deployment, serving, online inference, or distributed prediction.

Score: 

Evidence source: 

Evidence note: 

### RAY05 — Resource and accelerator scheduling

Critical: False

Supports allocation or scheduling of CPU, GPU, memory, or other constrained resources.

Score: 

Evidence source: 

Evidence note: 

### RAY06 — Parallel pipeline or task execution

Critical: False

Supports task, pipeline, actor, stage, or equivalent parallel execution structures.

Score: 

Evidence source: 

Evidence note: 

## Retrieved README

# Deploy BERT for Sentiment Analsysi with FastAPI

Deploy a pre-trained BERT model for Sentiment Analysis as a REST API using FastAPI

## Demo

The model is trained to classify sentiment (negative, neutral, and positive) on a custom dataset from app reviews on Google Play. Here's a sample request to the API:

```bash
http POST http://127.0.0.1:8000/predict text="Good basic lists, i would like to create more lists, but the annual fee for unlimited lists is too out there"
```

The response you'll get looks something like this:

```js
{
    "confidence": 0.9999083280563354,
    "probabilities": {
        "negative": 3.563107020454481e-05,
        "neutral": 0.9999083280563354,
        "positive": 5.596495248028077e-05
    },
    "sentiment": "neutral"
}
```

You can also [read the complete tutorial here](https://www.curiousily.com/posts/deploy-bert-for-sentiment-analysis-as-rest-api-using-pytorch-transformers-by-hugging-face-and-fastapi/)

## Installation

Clone this repo:

```sh
git clone git@github.com:curiousily/Deploy-BERT-for-Sentiment-Analysis-with-FastAPI.git
cd Deploy-BERT-for-Sentiment-Analysis-with-FastAPI
```

Install the dependencies:

```sh
pipenv install --dev
```

Download the pre-trained model:

```sh
bin/download_model
```

## Test the setup

Start the HTTP server:

```sh
bin/start_server
```

Send a test request:

```sh
bin/test_request
```

## License

MIT
