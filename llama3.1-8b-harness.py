#!/usr/bin/env python3
"""
Lightweight Inference Harness for LLaMA 3.1-8B
===============================================
Author: Pentagon Team @ops
Model: LLaMA 3.1-8B
Engine: PyTorch + bitsandbytes (4-bit quantization)
Target: RTX 4070 Super (12GB VRAM)

Features:
- 4-bit quantization via bitsandbytes (nf4 format)
- Dynamic batching with per-request memory budgeting
- Memory profiling with nsys/pytorch-profiler hooks
- Context length up to 8192 tokens
- Multi-GPU tensor parallelism (if available)

Usage:
    python llama3.1-8b-harness.py \
        --model-path /path/to/llama3.1-8B \
        --max-len 4096 \
        --batch-size 4 \
        --memory-threshold 8.5GB
"""

import os
import json
import time
import torch
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

# ============================================================================
# IMPORTS
# ============================================================================
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    PreTrainedTokenizer,
    StoppingCriteria,
    StoppingCriteriaList
)

# bitsandbytes for 4-bit quantization
try:
    import bitsandbytes as bnb
except ImportError:
    print("ERROR: bitsandbytes not installed. Run: pip install bitsandbytes")
    raise

# Memory profiling tools
try:
    from torch.utils import profiler as profiler_module
except ImportError:
    profiler_module = None

# ============================================================================
# CONFIGURATION
# ============================================================================
class Llama3HarnessConfig:
    """Configuration for the LLaMA 3.1-8B inference harness."""
    
    # Model paths
    model_path: str = "/path/to/llama3.1-8B"
    checkpoint_path: Optional[str] = None
    
    # Quantization
    quantize_4bit: bool = True
    load_in_8bit: bool = False  # Alternative if 4-bit fails
    
    # Quantization parameters (bitsandbytes)
    llm_int8_kwargs: Dict[str, Any] = {
        "inference_mode": False,
        "no_split_copy_weight": False,
        "quant_type": "nf4",  # Normalized float4
    }
    bnb_4bit_compute_dtype: torch.dtype = torch.float16  # Match hardware
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True  # Better compression
    
    # Model dimensions
    torch_dtype: torch.dtype = torch.float16
    device_map: str = "auto"  # Auto-assign to available GPUs
    
    # Inference parameters
    max_seq_length: int = 4096
    pad_token_id: int = 128000  # LLaMA 3.1 special PAD token
    eos_token_id: int = 128001  # LLaMA 3.1 special EOS token
    pad_token: Optional[str] = None
    
    # Batching
    max_batch_size: int = 4
    max_num_seqs: int = 8  # Allow up to 8 sequences per batch
    
    # Memory constraints
    max_memory_gb: float = 8.5  # WSL2 safety margin
    mem_budget_per_seq: float = 2.0  # GB per sequence budget
    
    # Generation parameters
    do_sample: bool = True
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    max_new_tokens: int = 512
    min_new_tokens: int = 1
    repetition_penalty: float = 1.1
    no_repeat_ngram_size: int = 0
    
    # Profiling
    enable_memory_profiling: bool = False
    profile_dir: Optional[str] = None
    
    # Output
    verbose: bool = True
    
    # ========================================================================
    # HELPER: Load checkpoint if not specified
    # ========================================================================
    
    def get_checkpoint_path(self) -> str:
        """Resolve the actual checkpoint path."""
        if self.checkpoint_path:
            return self.checkpoint_path
        return self.model_path
    
    # ========================================================================
    # TOKENIZER
    # ========================================================================
    
    def get_tokenizer(self) -> PreTrainedTokenizer:
        """Load or create tokenizer for LLaMA 3.1-8B."""
        # LLaMA 3.1 uses special padding/eos tokens
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=True,
            cache_dir="./.cache/llama3.1-tokenizer",
        )
        
        # Set padding and special tokens
        tokenizer.padding_side = "right"
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = self.pad_token_id
        tokenizer.eos_token_id = self.eos_token_id
        
        # Handle special PAD token if specified
        if self.pad_token:
            tokenizer.pad_token = self.pad_token
        
        return tokenizer
    
    # ========================================================================
    # MODEL LOADING (4-bit quantization)
    # ========================================================================
    
    def create_model(self) -> torch.nn.Module:
        """Load LLaMA 3.1-8B model with 4-bit quantization."""
        if not self.quantize_4bit:
            raise NotImplementedError("4-bit quantization via bitsandbytes required for LLaMA 3.1-8B.")
        
        model = AutoModelForCausalLM.from_pretrained(
            self.get_checkpoint_path(),
            quantization_config=self.llm_int8_kwargs,
            torch_dtype=self.torch_dtype,
            device_map=self.device_map,
            low_cpu_mem_usage=True,
            # bitsandbytes-specific kwargs
            load_in_4bit=self.quantize_4bit,
            load_in_8bit=self.load_in_8bit,
            quantization_config={
                "bnb_4bit_compute_dtype": self.bnb_4bit_compute_dtype,
                "bnb_4bit_quant_type": self.bnb_4bit_quant_type,
                "bnb_4bit_use_double_quant": self.bnb_4bit_use_double_quant,
            },
            trust_remote_code=True,
            cache_dir="./.cache/llama3.1-model",
        )
        
        # Ensure model is in evaluation mode
        model.eval()
        return model
    
    # ========================================================================
    # TEXT PROCESSING
    # ========================================================================
    
    def process_prompt(self, prompt: str, context: Optional[str] = None) -> Tuple[List[int], torch.Tensor]:
        """
        Process a prompt into tokens and prepare for generation.
        
        Args:
            prompt: User input string
            context: Optional conversation history context
            
        Returns:
            Tuple of (input_ids, attention_mask) tensors
        """
        if context:
            full_text = f"[INST]{context}[/INST] {prompt}"
        else:
            full_text = f"[INST]{prompt}[/INST]"
        
        # Tokenize
        input_ids = self.tokenizer.encode(full_text, return_tensors="pt")
        attention_mask = input_ids.bool()
        
        return input_ids, attention_mask
    
    # ========================================================================
    # GENERATION (with memory budgeting)
    # ========================================================================
    
    def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: Optional[int] = None,
        verbose: bool = False,
    ) -> str:
        """
        Generate completion for a given prompt.
        
        Args:
            prompt: User input
            context: Optional conversation context
            max_tokens: Override max_new_tokens if specified
            verbose: Print progress
            
        Returns:
            Generated completion string
        """
        if max_tokens:
            self.max_new_tokens = max_tokens
        
        # Process prompt
        input_ids, attention_mask = self.process_prompt(prompt, context)
        
        if verbose:
            print(f"[INFO] Input tokens: {input_ids.shape}")
        
        # Generate
        with torch.no_grad():
            # Use generation config with our parameters
            generation_kwargs = {
                "max_new_tokens": self.max_new_tokens,
                "min_new_tokens": self.min_new_tokens,
                "do_sample": self.do_sample,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "repetition_penalty": self.repetition_penalty,
                "no_repeat_ngram_size": self.no_repeat_ngram_size,
                "pad_token_id": self.pad_token_id,
                "eos_token_id": self.eos_token_id,
            }
            
            # Call model
            outputs = self.model.generate(
                input_ids,
                attention_mask=attention_mask,
                **generation_kwargs,
            )
        
        # Decode output
        generated_ids = outputs[0, input_ids.shape[1]:]
        generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        
        if verbose:
            print(f"[INFO] Generated {len(generated_ids)} tokens")
        
        return generated_text
    
    # ========================================================================
    # BATCHING (dynamic with memory profiling)
    # ========================================================================
    
    def batched_generate(
        self,
        prompts: List[Tuple[str, Optional[str]]],  # [(prompt, context), ...]
        batch_size: Optional[int] = None,
        verbose: bool = False,
    ) -> List[str]:
        """
        Generate completions for multiple prompts with dynamic batching.
        
        Args:
            prompts: List of (prompt, context) tuples
            batch_size: Override max_batch_size if specified
            verbose: Print progress
            
        Returns:
            List of generated completions
        """
        if batch_size:
            self.max_batch_size = batch_size
        
        if not prompts:
            return []
        
        # Collect and batch
        all_completions = []
        batch = []
        current_vram = self.get_current_vram_gb()
        budget = self.mem_budget_per_seq * self.max_batch_size
        
        for prompt, context in prompts:
            # Check memory budget before adding
            if current_vram > budget:
                if batch:
                    # Generate current batch
                    batch_completions = self._generate_batch(batch, verbose=verbose)
                    all_completions.extend(batch_completions)
                    batch = []
                current_vram = self.get_current_vram_gb()
            
            batch.append((prompt, context))
            
            if len(batch) >= self.max_batch_size:
                batch_completions = self._generate_batch(batch, verbose=verbose)
                all_completions.extend(batch_completions)
                batch = []
                current_vram = self.get_current_vram_gb()
        
        # Process remaining batch
        if batch:
            batch_completions = self._generate_batch(batch, verbose=verbose)
            all_completions.extend(batch_completions)
        
        return all_completions
    
    def _generate_batch(self, batch: List[Tuple[str, Optional[str]]], verbose: bool = False) -> List[str]:
        """
        Generate completions for a single batch of prompts.
        
        This uses the model's native batch generation.
        """
        # Create batch input
        all_prompts = [p for p, _ in batch]
        all_contexts = [c for _, c in batch]
        
        # Process all prompts
        input_ids_list = []
        attention_mask_list = []
        
        for prompt, context in batch:
            input_ids, attention_mask = self.process_prompt(prompt, context)
            input_ids_list.append(input_ids)
            attention_mask_list.append(attention_mask)
        
        # Stack tensors for batch generation
        input_ids = torch.cat(input_ids_list, dim=0)
        attention_mask = torch.cat(attention_mask_list, dim=0)
        
        # Generation kwargs
        generation_kwargs = {
            "max_new_tokens": self.max_new_tokens,
            "min_new_tokens": self.min_new_tokens,
            "do_sample": self.do_sample,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repetition_penalty": self.repetition_penalty,
            "no_repeat_ngram_size": self.no_repeat_ngram_size,
            "pad_token_id": self.pad_token_id,
            "eos_token_id": self.eos_token_id,
        }
        
        # Generate batch
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids,
                attention_mask=attention_mask,
                **generation_kwargs,
            )
        
        # Decode all outputs
        completions = []
        for i, (prompt, _) in enumerate(batch):
            input_len = input_ids.shape[1]
            output_len = outputs[i].shape[0]
            generated_ids = outputs[i, input_len:]
            generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
            completions.append(generated_text)
        
        if verbose:
            print(f"[INFO] Batch generated {len(batch)} completions")
        
        return completions
    
    # ========================================================================
    # MEMORY PROFILING
    # ========================================================================
    
    def get_current_vram_gb(self) -> float:
        """Get current VRAM usage in GB."""
        if torch.cuda.is_available():
            free_memory = torch.cuda.mem_get_info()[0]  # Free memory in bytes
            total_memory = torch.cuda.get_device_properties(0).total_memory
            used_memory = total_memory - free_memory
            return used_memory / 1e9  # Convert to GB
        return 0.0
    
    def profile_generation(self, prompt: str, context: Optional[str] = None):
        """
        Profile a single generation pass.
        
        Note: Profiling can be expensive. Only use for debugging.
        """
        if not self.enable_memory_profiling:
            print("[WARNING] Profiling disabled. Set enable_memory_profiling=True.")
            return
        
        # Create profiler
        if profiler_module:
            with profiler_module.profiler.profile(
                "memory_profile",
                record_shapes=True,
                profile_memory=True,
                with_flops=True,
            ) as prof:
                # Run generation (use a small prompt for profiling)
                _ = self.generate(prompt, context)
        
        if profiler_module:
            # Get profiling results
            print(f"[INFO] Profiling completed. See {self.profile_dir}")
    
    # ========================================================================
    # CONVERSATION MANAGEMENT
    # ========================================================================
    
    def prepare_conversation(self, history: List[Dict[str, str]]) -> str:
        """
        Convert conversation history to LLaMA 3.1 format.
        
        Args:
            history: List of {"role": "user|assistant", "content": str}
            
        Returns:
            Formatted prompt string
        """
        if not history:
            return ""
        
        messages = []
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            # Map roles to LLaMA 3.1 format
            if role == "user":
                messages.append(f"[INST]{content}[/INST]")
            elif role == "assistant":
                messages.append(content)
        
        return "\n\n".join(messages)
    
    def get_conversation_memory(self, history: List[Dict[str, str]], max_tokens: int = 4096) -> Tuple[str, List[Dict[str, str]]]:
        """
        Get conversation memory with token budgeting.
        
        Args:
            history: Full conversation history
            max_tokens: Maximum tokens to keep
            
        Returns:
            Tuple of (context, remaining_history)
        """
        # This is a simplified implementation
        # For production, use a sliding window or RAG
        return "", history
    
    # ========================================================================
    # TOOL CALLING SUPPORT (for LLaMA 3.1)
    # ========================================================================
    
    def prepare_tool_call(self, tools: List[Dict], prompt: str) -> str:
        """
        Add tool definitions to prompt for LLaMA 3.1 tool calling.
        
        Args:
            tools: List of tool definitions with name, description, parameters
            prompt: Base prompt
            
        Returns:
            Prompt with tool definitions appended
        """
        if not tools:
            return prompt
        
        tool_markdown = "### Available Tools\n\n"
        for tool in tools:
            name = tool.get("name", "")
            description = tool.get("description", "")
            parameters = tool.get("parameters", {})
            
            tool_markdown += f"**{name}**\n{description}\n\nParameters:\n"
            for param_name, param_def in parameters.items():
                tool_markdown += f"  - {param_name}: {param_def.get('type', 'string')}\n"
            
            tool_markdown += "---\n\n"
        
        return prompt + f"\n\nYou may use these tools: {tool_markdown}"
    
    # ========================================================================
    # MODEL CHECKPOINT UPDATES
    # ========================================================================
    
    def update_checkpoint(self, new_path: str):
        """
        Update model checkpoint path (for model updates).
        
        Note: You must call create_model() again after this.
        """
        self.model_path = new_path
        self.checkpoint_path = new_path
    
    # ========================================================================
    # GRADIENT CHECKPOINTING (optional for memory efficiency)
    # ========================================================================
    
    def enable_gradient_checkpointing(self):
        """
        Enable gradient checkpointing for memory efficiency.
        
        Warning: Slows down training. For inference-only use case, skip this.
        """
        try:
            for module in self.model.modules():
                if hasattr(module, "enable_gradient_checkpointing"):
                    module.enable_gradient_checkpointing()
            print("[INFO] Gradient checkpointing enabled.")
        except Exception as e:
            print(f"[ERROR] Failed to enable gradient checkpointing: {e}")
    
    # ========================================================================
    # MAIN (for command-line usage)
    # ========================================================================
    
    def run_example(self):
        """
        Run an example inference pass.
        
        This function is for demonstration. Call generate() directly in production.
        """
        print("=" * 60)
        print("LLaMA 3.1-8B Inference Harness - Example Usage")
        print("=" * 60)
        
        # Initialize config
        config = Llama3HarnessConfig(
            model_path="/path/to/llama3.1-8B",  # Replace with actual path
            max_seq_length=4096,
            max_batch_size=4,
            memory_threshold=8.5,
            verbose=True,
        )
        
        # Load model
        print("[INFO] Loading model...")
        config.model = config.create_model()
        config.tokenizer = config.get_tokenizer()
        
        # Example prompt
        prompt = "Explain quantum computing in simple terms."
        
        # Generate
        print(f"[INFO] Prompt: {prompt}")
        response = config.generate(prompt)
        
        print(f"\n[RESULT] Response:\n{response}")
        
        return response
    
    # ========================================================================
    # DEBUGGING
    # ========================================================================
    
    def print_model_stats(self):
        """Print model statistics for debugging."""
        print("\n[INFO] Model Statistics:")
        print(f"  Device: {next(self.model.parameters()).device}")
        if torch.cuda.is_available():
            total_memory = torch.cuda.get_device_properties(0).total_memory
            print(f"  VRAM: {total_memory / 1e9:.2f} GB ({total_memory / 1024**3:.2f} GiB)")
        
        # Count parameters
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        print(f"  Total Parameters: {total_params / 1e6:.2f}M ({total_params / 1e6}M)")
        print(f"  Trainable Parameters: {trainable_params / 1e6:.2f}M")
        
        # Check quantization
        for name, param in self.model.named_parameters():
            if param.device.type == "cuda":
                print(f"  {name}: device={param.device}, dtype={param.dtype}")
        
        print("=" * 60)
    
    # ========================================================================
    # CLEANUP
    # ========================================================================
    
    def cleanup(self):
        """Release model from memory (for GPU freeing)."""
        del self.model
        del self.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("[INFO] Model cleaned up.")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="LLaMA 3.1-8B Inference Harness")
    parser.add_argument("--model-path", type=str, default="/path/to/llama3.1-8B")
    parser.add_argument("--max-len", type=int, default=4096)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--memory-threshold", type=float, default=8.5)
    parser.add_argument("--prompt", type=str, default="Explain quantum computing.")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--verbose", action="store_true")
    
    args = parser.parse_args()
    
    # Create config
    config = Llama3HarnessConfig(
        model_path=args.model_path,
        max_seq_length=args.max_len,
        max_batch_size=args.batch_size,
        max_memory_gb=args.memory_threshold,
        temperature=args.temperature,
        verbose=args.verbose,
    )
    
    # Load model
    config.model = config.create_model()
    config.tokenizer = config.get_tokenizer()
    
    # Print stats
    if args.verbose:
        config.print_model_stats()
    
    # Generate
    response = config.generate(args.prompt)
    
    # Output
    print("\n[OUTPUT]")
    print(response)
    
    # Cleanup
    config.cleanup()
    
    # ========================================================================
    # END OF FILE
    # ========================================================================
