"""Reproducible PyTorch training and transparent synthetic evaluation."""
from __future__ import annotations
import argparse, json, random
from datetime import datetime, timezone
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np, torch
from torch import nn
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import train_test_split
from ai.dataset import CLASSES, FEATURES, generate_dataset

class PVConditionNet(nn.Module):
    def __init__(self, input_size: int = len(FEATURES), output_size: int = len(CLASSES)):
        super().__init__(); self.layers = nn.Sequential(nn.Linear(input_size, 24), nn.ReLU(), nn.Dropout(.08), nn.Linear(24, output_size))
    def forward(self, features): return self.layers(features)

def train_and_evaluate(output_dir: str | Path = "models", seed: int = 42, epochs: int = 180) -> dict:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.use_deterministic_algorithms(True, warn_only=True)
    frame = generate_dataset(seed=seed); Path("data").mkdir(exist_ok=True); frame.to_csv("data/synthetic_pv_dataset.csv", index=False)
    x=frame[FEATURES].to_numpy(np.float32); y=frame.condition.map(dict(zip(CLASSES, range(len(CLASSES))))).to_numpy()
    xt,xv,yt,yv=train_test_split(x,y,test_size=.25,random_state=seed,stratify=y); mean,std=xt.mean(0),xt.std(0); std[std==0]=1; xt=(xt-mean)/std; xv=(xv-mean)/std
    model=PVConditionNet(); opt=torch.optim.Adam(model.parameters(),lr=.008,weight_decay=1e-4); loss=nn.CrossEntropyLoss(); tx,ty=torch.tensor(xt),torch.tensor(yt,dtype=torch.long)
    model.train()
    for _ in range(epochs): opt.zero_grad(); value=loss(model(tx),ty); value.backward(); opt.step()
    model.eval()
    with torch.no_grad(): pred=model(torch.tensor(xv)).argmax(1).numpy()
    report=classification_report(yv,pred,target_names=CLASSES,output_dict=True,zero_division=0); matrix=confusion_matrix(yv,pred).tolist()
    metrics={"data_origin":"synthetic PV simulation; not field/hardware validation","seed":seed,"train_samples":len(yt),"test_samples":len(yv),"test_accuracy":float(accuracy_score(yv,pred)),"classification_report":report,"confusion_matrix":matrix}
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    metadata={"model_type":"PVConditionNet (8→24→5)","version":"1.0.0","features":FEATURES,"class_mapping":dict(enumerate(CLASSES)),"dataset_type":"reproducible synthetic PV simulation","created_utc":datetime.now(timezone.utc).isoformat(),"disclaimer":"Synthetic metrics do not represent field performance."}
    torch.save({"state_dict":model.state_dict(),"feature_mean":mean,"feature_std":std,"features":FEATURES,"classes":CLASSES,"metrics":metrics,"metadata":metadata},out/"pv_condition_classifier.pt")
    (out/"training_metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8"); (out/"model_metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    (out/"preprocessor.json").write_text(json.dumps({"features":FEATURES,"mean":mean.tolist(),"std":std.tolist()}),encoding="utf-8")
    figure,axis=plt.subplots(figsize=(7,5)); ConfusionMatrixDisplay(np.array(matrix),display_labels=CLASSES).plot(ax=axis,xticks_rotation=30,colorbar=False); figure.tight_layout(); figure.savefig(out/"confusion_matrix.png",dpi=160); plt.close(figure)
    return metrics

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--epochs",type=int,default=180); parser.add_argument("--seed",type=int,default=42); args=parser.parse_args(); print(json.dumps(train_and_evaluate(seed=args.seed,epochs=args.epochs),indent=2))
