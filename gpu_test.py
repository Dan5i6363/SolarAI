"""Optional manual GPU stress utility; it is intentionally not a pytest test."""
import time
import torch

def run_gpu_test(seconds: int = 30) -> None:
    if not torch.cuda.is_available(): raise RuntimeError("CUDA GPU is not available")
    print("GPU:", torch.cuda.get_device_name(0)); x=torch.randn(12000,12000,device="cuda")
    print(f"GPU stress test running for {seconds} seconds")
    end=time.time()+seconds
    while time.time()<end: _=x@x; torch.cuda.synchronize()
    print("GPU stress test complete")

if __name__ == "__main__": run_gpu_test()
