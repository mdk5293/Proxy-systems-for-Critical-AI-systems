# CAIS Proxy-Fitness Evidence Packet

- Anchor: `serengil-deepface`
- Candidate: `cavalleria/cavaface`
- Repository URL: https://github.com/cavalleria/cavaface

## Repository metadata

Description: face recognition training project(pytorch)

Topics: face-recognition, pytorch, network, loss, arcnegface, arcface, resnest, attention-irse, apex, randaugment, mixup, dataparallel, model-parallel, resnet-irse, curricularface, cosface, amsoftmax, circleloss, ghostnet, efficientnet

## Frozen rubric

### DFC01 — Face detection and representation

Critical: True

Supports detecting faces and producing representations, embeddings, or equivalent identity-oriented features.

Score: 

Evidence source: 

Evidence note: 

### DFC02 — Identity verification or matching

Critical: True

Supports comparing identities using similarity, distance, thresholds, verification, or recognition.

Score: 

Evidence source: 

Evidence note: 

### DFC03 — Spoofing or authenticity resistance

Critical: False

Supports anti-spoofing, liveness, authenticity checking, or equivalent presentation-attack testing.

Score: 

Evidence source: 

Evidence note: 

### DFC04 — Model or detector variability

Critical: False

Supports multiple models, detector backends, recognition approaches, or configurable processing pipelines.

Score: 

Evidence source: 

Evidence note: 

### DFC05 — Threshold and confidence behavior

Critical: False

Supports threshold, confidence, distance, calibration, or comparable decision-boundary evaluation.

Score: 

Evidence source: 

Evidence note: 

### DFC06 — Service or application integration

Critical: False

Supports API, service, database, streaming, or application-level integration of face-analysis functionality.

Score: 

Evidence source: 

Evidence note: 

## Retrieved README

# cavaface: A Pytorch Training Framework for Deep Face Recognition

[![python-url](https://img.shields.io/badge/Python-3.x-red.svg)](https://www.python.org/)
[![pytorch-url](https://img.shields.io/badge/Pytorch-1.9-blue.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Docker Pulls](https://img.shields.io/docker/pulls/cavall/cavaface_env?logo=docker).

By Yaobin Li and Liying Chi

## Introduction

This repo provides a high-performance distribute parallel training framework for face recognition with pytorch, including various backbones (e.g., ResNet, IR, IR-SE, ResNeXt, AttentionNet-IR-SE, ResNeSt, HRNet, etc.), various losses (e.g., Softmax, Focal, SphereFace, CosFace, AmSoftmax, ArcFace, ArcNegFace, CurricularFace, Li-Arcface, QAMFace, etc.), various data augmentation(e.g., RandomErasing, Mixup, RandAugment, Cutout, CutMix, etc.) and bags of tricks for improving performance (e.g., FP16 training(apex), Label smooth, LR warmup, etc)

## Features

<details open>
<summary>(click to collapse)</summary>

* **Backbone**
  * [x] ResNet(IR-SE)
  * [x] ResNeXt
  * [x] DenseNet
  * [x] MobileFaceNet
  * [x] MobileNetV3
  * [x] EfficientNet
  * [x] ProxylessNas
  * [x] GhostNet
  * [x] AttentionNet-IRSE
  * [x] ResNeSt
  * [x] ReXNet
  * [x] MobileNetV2
  * [x] MobileNeXt
* **Attention Module**
  * [x] SE
  * [x] CBAM
  * [x] ECA
  * [x] GCT
* **Loss**
  * [x] Softmax
  * [x] SphereFace
  * [x] AMSoftmax
  * [x] CosFace
  * [x] ArcFace
  * [x] Combined Loss
  * [x] AdaCos
  * [x] SV-X-Softmax
  * [x] CurricularFace
  * [x] ArcNegFace
  * [x] Li-Arcface
  * [x] QAMFace
  * [x] Circle Loss 
* **Parallel Training**
  * [x] DDP
  * [x] Model Parallel
* **Automatic Mixed Precision**
  * [x] AMP
* **Optimizer**
  * [x] LRScheduler([faireq](https://github.com/pytorch/fairseq/tree/master/fairseq/optim/lr_scheduler),[rwightman](https://github.com/rwightman/pytorch-image-models/tree/master/timm/scheduler))
  * [x] Optim(SGD,Adam,RAdam,LookAhead,Ranger,AdamP,SGDP)
  * [x] ZeRO
* **[Data Augmentation**
  * [x] RandomErasing
  * [x] Mixup
  * [x] RandAugment
  * [x] Cutout
  * [x] CutMix
  * [x] Colorjitter 
* **Distillation**
  * [ ] KnowledgeDistillation
  * [ ] Multi Feature KD
* **Bag of Tricks**
  * [x] Label smooth
  * [x] LR warmup

</details>

## Installation

See [INSTALL.md](https://github.com/cavalleria/cavaface.pytorch/blob/master/docs/INSTALL.md).

## Quick start

See [GETTING_STARTED.md](https://github.com/cavalleria/cavaface.pytorch/blob/master/docs/GETTING_STARTED.md).

## Model Zoo and Benchmark

See [MODEL_ZOO.md](https://github.com/cavalleria/cavaface.pytorch/blob/master/docs/MODEL_ZOO.md).

## License

cavaface is released under the [MIT license](https://github.com/cavalleria/cavaface.pytorch/blob/master/docs/LICENSE).

## Acknowledgement

* This repo is modified and adapted on these great repositories [face.evoLVe.PyTorch](https://github.com/ZhaoJ9014/face.evoLVe.PyTorch), [CurricularFace](https://github.com/HuangYG123/CurricularFace), [insightface](https://github.com/deepinsight/insightface) and [imgclsmob](https://github.com/osmr/imgclsmob/)
* The evaluation tools is developed by [Charrin](https://github.com/Charrin)

## Contact

```markdown
cavallyb@gmail.com
```
