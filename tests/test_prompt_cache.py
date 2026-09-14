"""Prompt caching on the models the agents use.

A tool loop resends the tools, the system prompt and the conversation on every
turn. These markers are what let that prefix bill as a cache read instead of
full-price input. Removing one fails nothing else in the suite and nothing at
run time: the bill just goes up. So it is pinned here.

The test checks the configuration only. Whether a real run hits the cache shows
up in its metrics, as `cache_read_tokens`.
"""

from linkedin_growth import config


def test_every_model_marks_the_system_prompt_and_the_conversation_for_caching(monkeypatch):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "sk-ant-test")

    for model_id in (config.MAIN_MODEL, config.FAST_MODEL):
        model = config.model(model_id)

        assert model.cache_system_prompt is True, model_id
        # The top-level field: Anthropic's automatic breakpoint on the last block.
        assert model.get_request_params()["cache_control"] == {"type": "ephemeral"}, model_id
