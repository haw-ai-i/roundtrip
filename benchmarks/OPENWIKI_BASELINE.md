OpenWiki baseline comparison
 comparing our agent's descriptions against documentation produced by OpenWiki
(github.com/langchain-ai/openwiki), a tool that generates agent-facing documentation for a
codebase. OpenWiki is built around OpenRouter, but since it is open source we pointed its
OpenAI provider at Gemini's OpenAI-compatible endpoint, so it runs on the same model family
(gemini-2.5-pro for documentation) as our benchmark. We then fed OpenWiki's generated
documentation through the identical regenerate + evaluate pipeline used for our own agent, so
the only variable is the source of the description.

Results (roundtrip fidelity, fraction of original tests passed):

  Fixture      OpenWiki    Our agent
  saferepr     0.00        0.73
  contains     0.67        1.00
  unitsystem   0.00        0.85

OpenWiki produces competent, readable documentation of each module's public interface, with
usage examples and API summaries. But because it documents the interface rather than a complete
specification for reconstruction, code regenerated from it omits internal details the tests
depend on. On saferepr it omitted the private helper _pformat_dispatch; on unitsystem it omitted
the class attribute _quantity_scale_factors_global; in both cases regeneration failed at import
or collection. On contains it regenerated most behavior but missed two tests.

Across all three fixtures OpenWiki's documentation yields lower regeneration fidelity than our
agent's descriptions. This supports the paper's central point: what a description needs for
regeneration is completeness, including the internal details (private functions, class
attributes, exact signatures) that human-facing documentation typically omits. Our describe
step is explicitly instructed to capture those; a general documentation tool is not.
