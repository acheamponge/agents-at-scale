from config import settings


def model_for(spec: str):
    provider, _, name = spec.partition(":")
    if provider != "crusoe":
        return spec
    try:
        import pydantic_ai.providers.crusoe
        return spec
    except ImportError:
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider
        return OpenAIChatModel(name, provider=OpenAIProvider(base_url=settings.llm_base_url, api_key=settings.crusoe_api_key))
