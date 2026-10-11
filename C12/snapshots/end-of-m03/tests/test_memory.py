from adapt.memory import estimate_gb, fits, inference_gb


def test_full_tuning_needs_16_bytes_per_parameter_before_activations():
    assert round(estimate_gb(1e9, "full fine-tuning (float32)"), 3) == 16.0
    assert not fits(estimate_gb(7e9, "full fine-tuning (float32)"), 80)
    assert fits(estimate_gb(7e9, "QLoRA, base in 4 bits"), 24)


def test_quantization_shrinks_the_weights_not_the_trained_part():
    assert inference_gb(134_515_008, "int4") * 8 == inference_gb(134_515_008, "float32")
    lora32 = estimate_gb(134_515_008, "LoRA, base in float32")
    lora4 = estimate_gb(134_515_008, "QLoRA, base in 4 bits")
    assert round(lora32 - lora4, 3) == round(134_515_008 * 3.5 / 1e9, 3)
