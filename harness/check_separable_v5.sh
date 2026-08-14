#!/bin/sh
set -eu

src="${1:-../recovered-session/wine-11.0/dlls/wined3d/glsl_shader.c}"

# The candidate must use Wine's resolved GL dispatch, never a second
# wglGetProcAddress path that can bypass the CrossOver GLES facade.
if rg -n 'wglGetProcAddress\("gl(ProgramParameteri|GenProgramPipelines|DeleteProgramPipelines|UseProgramStages|BindProgramPipeline|ActiveShaderProgram|ValidateProgramPipeline|GetProgramPipelineiv)' "$src"; then
    echo "direct separable lookup found" >&2
    exit 1
fi

for needle in \
    'mgs2_resolve_separable(gl_info)' \
    'entry->id = pipeline' \
    'mgs2_glBindProgramPipeline(0)' \
    'mgs2_glDeleteProgramPipelines'; do
    rg -F -q "$needle" "$src" || { echo "missing safety check: $needle" >&2; exit 1; }
done

echo "separable-v5 static safety checks: PASS"
