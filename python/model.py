import clip
import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
import yaml
from PIL import Image
import os


class Model:
    def __init__(
        self,
        settings_path: str = "./settings.yaml",
        weights_dir: str = "./weights",   # 👈 NEW
        device: str = None                # 👈 NEW (optional override)
    ):
        # Load settings
        with open(settings_path, "r") as file:
            self.settings = yaml.safe_load(file)

        # Device
        self.device = device or self.settings['model-settings']['device']

        # Model config
        self.model_name = self.settings['model-settings']['model-name']
        self.threshold = self.settings['model-settings']['prediction-threshold']
    
        model_path = os.path.join(weights_dir, "ViT-B-32.pt")

        # ✅ FORCE LOCAL WEIGHTS (NO DOWNLOAD)
        if not os.path.exists(weights_dir):
            raise Exception(f"Weights directory not found: {weights_dir}")

        print("✅ Loading CLIP from:", weights_dir)

        self.model, self.preprocess = clip.load(
            model_path,   # 👈 FORCE FILE PATH
            device=self.device
        )

        # Labels
        self.labels = self.settings['label-settings']['labels']
        self.labels_ = ['a photo of ' + label for label in self.labels]

        self.text_features = self.vectorize_text(self.labels_)
        self.default_label = self.settings['label-settings']['default-label']

    @torch.no_grad()
    def transform_image(self, image: np.ndarray):
        pil_image = Image.fromarray(image).convert('RGB')
        return self.preprocess(pil_image).unsqueeze(0).to(self.device)

    @torch.no_grad()
    def tokenize(self, text: list):
        return clip.tokenize(text).to(self.device)

    @torch.no_grad()
    def vectorize_text(self, text: list):
        tokens = self.tokenize(text)
        return self.model.encode_text(tokens)

    @torch.no_grad()
    def predict_(self, text_features, image_features):
        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        similarity = image_features @ text_features.T
        values, indices = similarity[0].topk(1)
        return values, indices

    @torch.no_grad()
    def predict(self, image: np.ndarray) -> dict:
        tf_image = self.transform_image(image)
        image_features = self.model.encode_image(tf_image)

        values, indices = self.predict_(
            text_features=self.text_features,
            image_features=image_features
        )

        label_index = indices[0].cpu().item()
        confidence = abs(values[0].cpu().item())

        label = self.default_label
        if confidence >= self.threshold:
            label = self.labels[label_index]

        return {
            "label": label,
            "confidence": confidence
        }

    @staticmethod
    def plot_image(image: np.ndarray, title_text: str):
        plt.figure(figsize=[13, 13])
        plt.title(title_text)
        plt.axis('off')
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        plt.imshow(image)