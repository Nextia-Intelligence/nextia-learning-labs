from adapt.params import LINEAR, load_config, lora_params, total_params


def test_parameter_counts_match_the_real_model():
    config = load_config()
    assert total_params(config) == 134_515_008
    assert lora_params(config, 8) == 460_800            # peft printed the same number
    assert lora_params(config, 8, LINEAR) == 2_442_240


def test_lora_grows_linearly_with_the_rank():
    config = load_config()
    assert lora_params(config, 16) == 2 * lora_params(config, 8)

