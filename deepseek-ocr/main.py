from transformers import AutoModel, AutoTokenizer
import torch
import os
import warnings

# Disable all autocast and mixed precision
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False

# Force CPU usage - aggressive monkey patching
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Hide CUDA devices

# Monkey patch to prevent CUDA calls
original_cuda = torch.Tensor.cuda
def fake_cuda(self, device=None, non_blocking=False, memory_format=torch.preserve_format):
    # Preserve integer and boolean types
    if self.dtype in [torch.int64, torch.int32, torch.long, torch.bool]:
        return self  # Keep integers and booleans as-is
    return self.float()  # Convert floats to float32 on CPU

# Patch bfloat16 conversion to float32
original_bfloat16 = torch.Tensor.bfloat16
def fake_bfloat16(self, memory_format=torch.preserve_format):
    # Preserve integer and boolean types
    if self.dtype in [torch.int64, torch.int32, torch.long, torch.bool]:
        return self  # Keep integers and booleans as-is
    return self.float()

torch.Tensor.cuda = fake_cuda
torch.Tensor.bfloat16 = fake_bfloat16
torch.cuda.is_available = lambda: False  # Override CUDA availability check

# Disable autocast globally
torch.autocast = lambda *args, **kwargs: torch.no_grad()

model_name = 'deepseek-ai/DeepSeek-OCR'

# Set device to CPU explicitly
device = torch.device("cpu")

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModel.from_pretrained(model_name, trust_remote_code=True, use_safetensors=True, torch_dtype=torch.float32)
model = model.eval().to(device).float()  # Ensure all parameters are float32

# prompt = "<image>\nFree OCR. "
prompt = "<image>\n<|grounding|>Convert the document to an object captring dates as a list, provider, facility, and any other relevant information in JSON format. "
image_file = 'input-files/patient-care-summary.png'
output_path = 'output'

# infer(self, tokenizer, prompt='', image_file='', output_path = ' ', base_size = 1024, image_size = 640, crop_mode = True, test_compress = False, save_results = False):

# Tiny: base_size = 512, image_size = 512, crop_mode = False
# Small: base_size = 640, image_size = 640, crop_mode = False
# Base: base_size = 1024, image_size = 1024, crop_mode = False
# Large: base_size = 1280, image_size = 1280, crop_mode = False

# Gundam: base_size = 1024, image_size = 640, crop_mode = True

res = model.infer(tokenizer, prompt=prompt, image_file=image_file, output_path = output_path, base_size = 1024, image_size = 640, crop_mode=True, save_results = True, test_compress = True)
