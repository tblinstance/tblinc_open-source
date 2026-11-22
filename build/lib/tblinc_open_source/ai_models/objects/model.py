"""24. ObjectDetectorModel: Multi-Object Region Proposal, NMS & Mahalanobis/Prototype Bounding-Box Detector."""

from __future__ import annotations

import math
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict


def _iou(box_a: list[int], box_b: list[int]) -> float:
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    if x2 < x1 or y2 < y1:
        return 0.0
    inter = float((x2 - x1 + 1) * (y2 - y1 + 1))
    area_a = float((box_a[2] - box_a[0] + 1) * (box_a[3] - box_a[1] + 1))
    area_b = float((box_b[2] - box_b[0] + 1) * (box_b[3] - box_b[1] + 1))
    return inter / max(1.0, area_a + area_b - inter)


def _nms(detections: list[dict[str, Any]], iou_threshold: float = 0.5) -> list[dict[str, Any]]:
    ordered = sorted(detections, key=lambda d: float(d.get("confidence", 0.0)), reverse=True)
    kept: list[dict[str, Any]] = []
    for cand in ordered:
        if all(_iou(cand["bbox"], k["bbox"]) < iou_threshold for k in kept):
            kept.append(cand)
    return kept


def _extract_components(grid: list[list[float]], threshold: float = 0.45) -> list[dict[str, Any]]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    visited = [[False] * w for _ in range(h)]
    regions: list[dict[str, Any]] = []

    for r in range(h):
        for c in range(w):
            if visited[r][c] or grid[r][c] < threshold:
                continue
            stack = [(r, c)]
            visited[r][c] = True
            pixels: list[tuple[int, int, float]] = []
            while stack:
                cr, cc = stack.pop()
                pixels.append((cr, cc, float(grid[cr][cc])))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and grid[nr][nc] >= threshold:
                        visited[nr][nc] = True
                        stack.append((nr, nc))
            rs = [p[0] for p in pixels]
            cs = [p[1] for p in pixels]
            y1, y2 = min(rs), max(rs)
            x1, x2 = min(cs), max(cs)
            bw = (x2 - x1) + 1
            bh = (y2 - y1) + 1
            area = len(pixels)
            fill_ratio = area / max(1, bw * bh)
            aspect = bw / max(1, bh)
            intensity = sum(p[2] for p in pixels) / max(1, area)
            regions.append(
                {
                    "bbox": [x1, y1, x2, y2],
                    "width": bw,
                    "height": bh,
                    "area": area,
                    "features": [float(area), float(aspect), float(fill_ratio), float(intensity)],
                }
            )
    return regions


@register_model
class ObjectDetectorModel(BaseAIModel):
    """2D region proposal + Non-Maximum Suppression (NMS) bounding-box object detector."""

    metadata = ModelMetadata(
        key="objects",
        name="Object Detection AI",
        category="Computer Vision",
        task="Multi-Object Bounding Box Detection",
        description="Detects multiple objects in 2D image grids with NMS and predicts [x1, y1, x2, y2] boxes & labels.",
        input_example={
            "image": [
                [0, 1, 1, 0, 0, 0, 0, 0],
                [0, 1, 1, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0, 1, 0, 0],
                [1, 1, 1, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0],
            ],
            "threshold": 0.45,
        },
        tags=["object-detection", "yolo", "bbox", "vision", "nms"],
    )

    def __init__(self, threshold: float = 0.45, iou_threshold: float = 0.5) -> None:
        super().__init__()
        self.threshold = threshold
        self.iou_threshold = iou_threshold
        self.prototypes: dict[str, list[float]] = {}

    def fit(self, prototypes: dict[str, list[float]] | None = None) -> ObjectDetectorModel:
        if prototypes:
            self.prototypes = {str(k): [float(v) for v in vec] for k, vec in prototypes.items()}
        else:
            # Features: [area, aspect_ratio (w/h), fill_ratio, mean_intensity]
            self.prototypes = {
                "square_box": [4.0, 1.0, 1.0, 1.0],
                "vertical_bar": [3.0, 0.33, 1.0, 1.0],
                "horizontal_bar": [4.0, 4.0, 1.0, 1.0],
                "dot_marker": [1.0, 1.0, 1.0, 1.0],
            }
        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = {
            "classes": sorted(self.prototypes),
            "threshold": self.threshold,
            "iou_threshold": self.iou_threshold,
        }
        return self

    def _classify_region(self, feats: list[float]) -> tuple[str, float, dict[str, float]]:
        scores: dict[str, float] = {}
        for lbl, proto in self.prototypes.items():
            dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(feats, proto)))
            scores[lbl] = round(1.0 / (1.0 + dist), 4)
        best_lbl = max(scores, key=lambda k: scores[k]) if scores else "object"
        return best_lbl, scores.get(best_lbl, 0.0), scores

    @timed_predict
    def predict(self, data: list[list[float]] | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("ObjectDetectorModel must be fitted before predict().")
        if isinstance(data, dict):
            image = [[float(px) for px in row] for row in data["image"]]
            thr = float(data.get("threshold", self.threshold))
        else:
            image = [[float(px) for px in row] for row in data]
            thr = self.threshold

        regions = _extract_components(image, threshold=thr)
        raw_detections: list[dict[str, Any]] = []
        for reg in regions:
            lbl, conf, class_scores = self._classify_region(reg["features"])
            raw_detections.append(
                {
                    "label": lbl,
                    "confidence": conf,
                    "bbox": reg["bbox"],
                    "area": reg["area"],
                    "class_scores": class_scores,
                }
            )
        detections = _nms(raw_detections, iou_threshold=self.iou_threshold)
        avg_conf = round(sum(d["confidence"] for d in detections) / max(1, len(detections)), 4) if detections else 0.0
        return PredictionResult(
            model=self.metadata.key,
            prediction=detections,
            confidence=avg_conf,
            details={"num_detections": len(detections), "labels": [d["label"] for d in detections]},
        )

    def get_state(self) -> dict[str, Any]:
        return {
            "threshold": self.threshold,
            "iou_threshold": self.iou_threshold,
            "prototypes": self.prototypes,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.threshold = float(state["threshold"])
        self.iou_threshold = float(state.get("iou_threshold", 0.5))
        self.prototypes = {str(k): [float(v) for v in vec] for k, vec in state["prototypes"].items()}

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        self.fit()
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
