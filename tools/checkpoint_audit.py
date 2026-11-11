#!/usr/bin/env python3
"""Inspect retained original checkpoint using safe PyTorch deserialization."""
import hashlib
import json
from pathlib import Path
import sys
import torch

path = Path(sys.argv[1])
state = torch.load(path, map_location='cpu', weights_only=True)
config = state.get('config')
if config is None:
    config = json.loads(path.with_name('model.config.json').read_text())
expected_version, expected_blocks = {384: (15, 10), 512: (17, 10), 768: (17, 11)}[int(sys.argv[2])]
if (config['version'] != expected_version or config['trunk_num_channels'] != int(sys.argv[2])
        or len(config['block_kind']) != expected_blocks):
    raise ValueError('Checkpoint architecture does not match adopted candidate')
if not state.get('model'):
    raise ValueError('Missing regular model state')


def tensors(values):
    result = {}
    for name, value in sorted(values.items()):
        if not isinstance(value, torch.Tensor):
            raise ValueError('Unexpected non-tensor state')
        if value.is_floating_point() and not torch.isfinite(value).all():
            raise ValueError('Nonfinite model state')
        raw = value.detach().cpu().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()
        result[name] = {'sha256': hashlib.sha256(raw).hexdigest(), 'dtype': str(value.dtype),
                        'shape': list(value.shape)}
    return result


# Reuse pinned native definitions to reject shape/config-compatible-looking but
# unloadable regular or SWA states. This performs no forward pass or update.
sys.path.insert(0, str(Path('source/katago-clean/python').resolve()))
from katago.train.load_model import load_model
load_model(str(path), use_swa=bool(state.get('swa_model')), device='cpu', verbose=False)

print(json.dumps({'checkpoint': str(path), 'config': config,
                  'regular': tensors(state['model']),
                  'swa': tensors(state['swa_model']) if state.get('swa_model') else None,
                  'swa_status': 'present' if state.get('swa_model') else 'absent',
                  'regular_equals_official': 'unknown',
                  'checkpoint_keys': sorted(state)}))
