from core.model_gateway import ModelGateway, ModelRequest, ModelProvider, ModelResponse
from core.model_gateway.capabilities import ModelCapability, ModelCapabilityRegistry
from core.model_gateway.fallback import ModelFallbackExecutor
from core.model_gateway.verification import ModelResponseVerifier
from core.model_gateway.external_capability import ExternalAICapability, ExternalAICapabilityRegistry

class Good(ModelProvider):
    name='good'; capabilities=(ModelCapability('reasoning'),)
    def generate(self, request): return ModelResponse('ok','good','g1',True)
class Bad(ModelProvider):
    name='bad'
    def generate(self, request): return ModelResponse('','bad','b1',False,'failed')

g=ModelGateway(); g.register_provider(Bad()); g.register_provider(Good())
assert ModelCapabilityRegistry(g._providers).supports('good','reasoning')
r=ModelFallbackExecutor(g).generate(ModelRequest('x'),['bad','good'])
assert r.response.success and r.response.provider=='good' and r.metadata['fallback_used']
assert ModelResponseVerifier().verify(r.response).valid
x=ExternalAICapabilityRegistry(); x.register(ExternalAICapability('external','vision','reference','test'))
assert not x.is_authority() and not x.grants_permission() and not x.executes_external_actions()
print('SAHIBEX PHASE W MODEL INDEPENDENCE EXPANSION TEST: PASS')
