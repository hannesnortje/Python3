import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification

# Load the MobileNet V2 model and processor
processor = AutoImageProcessor.from_pretrained("google/mobilenet_v2_1.0_224")
model = AutoModelForImageClassification.from_pretrained("google/mobilenet_v2_1.0_224")

# Set the model to evaluation mode
model.eval()

# Create dummy input for tracing (batch_size, channels, height, width)
dummy_input = torch.randn(1, 3, 224, 224)

# Export the model to ONNX
torch.onnx.export(
    model,
    dummy_input,
    "mobilenetv2.onnx",
    input_names=["input"],
    output_names=["output"],
    dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}}
)
