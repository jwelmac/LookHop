"""Tiny "laptop vs monitor" classifier.

Two logistic regressions: one on head pose (yaw, pitch) and one on iris
position. Head pose is the main vote; the iris vote is added with a smaller
weight so it can break ties when the head barely moves.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

FEATURE_NAMES = ("yaw", "pitch", "iris_h", "iris_v")
HEAD = [0, 1]
IRIS = [2, 3]
LOGIT_CLIP = 8.0
LAPTOP, MONITOR = 1, 0


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


class LogReg:
    def __init__(self, mu, sd, w, b):
        self.mu = np.asarray(mu, float)
        self.sd = np.asarray(sd, float)
        self.w = np.asarray(w, float)
        self.b = float(b)

    @classmethod
    def fit(cls, X, y, l2: float = 1.0, iters: int = 60) -> "LogReg":
        """Ridge logistic regression via Newton steps on standardized features."""
        X = np.asarray(X, float)
        y = np.asarray(y, float)
        mu = X.mean(axis=0)
        sd = X.std(axis=0)
        sd[sd < 1e-6] = 1e-6
        Z = np.hstack([(X - mu) / sd, np.ones((len(X), 1))])
        d = Z.shape[1]
        reg = np.eye(d)
        reg[-1, -1] = 0.0  # don't shrink the bias
        w = np.zeros(d)
        for _ in range(iters):
            p = sigmoid(Z @ w)
            grad = Z.T @ (p - y) + l2 * reg @ w
            hess = (Z * (p * (1 - p))[:, None]).T @ Z + l2 * reg + 1e-6 * np.eye(d)
            step = np.linalg.solve(hess, grad)
            w -= step
            if np.max(np.abs(step)) < 1e-8:
                break
        return cls(mu, sd, w[:-1], w[-1])

    def logit(self, X) -> np.ndarray:
        Z = (np.atleast_2d(np.asarray(X, float)) - self.mu) / self.sd
        return np.clip(Z @ self.w + self.b, -LOGIT_CLIP, LOGIT_CLIP)

    def to_dict(self) -> dict:
        return {"mu": self.mu.tolist(), "sd": self.sd.tolist(), "w": self.w.tolist(), "b": self.b}

    @classmethod
    def from_dict(cls, d: dict) -> "LogReg":
        return cls(d["mu"], d["sd"], d["w"], d["b"])


class GazeModel:
    def __init__(self, head: LogReg, iris: LogReg, iris_weight: float, meta: dict | None = None):
        self.head = head
        self.iris = iris
        self.iris_weight = iris_weight
        self.meta = meta or {}

    @classmethod
    def train(cls, X, y, iris_weight: float, meta: dict | None = None) -> "GazeModel":
        X = np.asarray(X, float)
        return cls(LogReg.fit(X[:, HEAD], y), LogReg.fit(X[:, IRIS], y), iris_weight, meta)

    def logit(self, X) -> np.ndarray:
        X = np.atleast_2d(np.asarray(X, float))
        return self.head.logit(X[:, HEAD]) + self.iris_weight * self.iris.logit(X[:, IRIS])

    def p_laptop(self, features) -> float:
        return float(sigmoid(self.logit(features))[0])

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "features": FEATURE_NAMES,
            "head": self.head.to_dict(),
            "iris": self.iris.to_dict(),
            "meta": self.meta,
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(path)

    @classmethod
    def load(cls, path: Path, iris_weight: float) -> "GazeModel":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(LogReg.from_dict(data["head"]), LogReg.from_dict(data["iris"]),
                   iris_weight, data.get("meta", {}))


def cross_validate(X, y, groups, iris_weight: float) -> dict:
    """Leave-one-calibration-point-out accuracy, per class, for combined/head/iris.
    More honest than training accuracy: each point is scored by a model that never saw it."""
    X, y, groups = np.asarray(X, float), np.asarray(y, int), np.asarray(groups)
    logits = {k: np.full(len(y), np.nan) for k in ("combined", "head", "iris")}
    for g in np.unique(groups):
        test = groups == g
        train = ~test
        if len(np.unique(y[train])) < 2:
            continue
        m = GazeModel.train(X[train], y[train], iris_weight)
        logits["head"][test] = m.head.logit(X[test][:, HEAD])
        logits["iris"][test] = m.iris.logit(X[test][:, IRIS])
        logits["combined"][test] = m.logit(X[test])

    out = {}
    for name, z in logits.items():
        ok = ~np.isnan(z)
        pred = (z > 0).astype(int)
        per = {}
        for label, cls_name in ((LAPTOP, "laptop"), (MONITOR, "monitor")):
            sel = ok & (y == label)
            per[cls_name] = float(np.mean(pred[sel] == label)) if sel.any() else float("nan")
        out[name] = per
    return out


def make_meta(glasses: bool, n_laptop: int, n_monitor: int, accuracy: dict) -> dict:
    return {
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "glasses": glasses,
        "samples": {"laptop": n_laptop, "monitor": n_monitor},
        "accuracy": accuracy,
    }
