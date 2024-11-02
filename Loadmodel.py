import torch
from transformers import AutoModelForImageClassification, AutoFeatureExtractor

# Load pre-trained ResNet-50 model from Hugging Face
model_name = "microsoft/resnet-50"
model = AutoModelForImageClassification.from_pretrained(model_name)
extractor = AutoFeatureExtractor.from_pretrained(model_name)

# Create dummy input that matches the input size of the model
dummy_input = torch.randn(1, 3, 224, 224)  # Batch size of 1, 3 color channels, 224x224 image size

# Export the model to ONNX format
torch.onnx.export(model, dummy_input, "resnet50.onnx", 
                  input_names=["input"], output_names=["output"],
                  opset_version=11)
