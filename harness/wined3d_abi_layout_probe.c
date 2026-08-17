/* WINED3D_ABI_LAYOUT_PROBE
 *
 * Answers one question with a compiler rather than an argument: does the same
 * declaration lay out identically for the i386 PE that runs today and for the
 * armhf target a native helper would be built as?  Only layout matters here, so
 * the Windows scalar typedefs are stubbed at their real widths, which are the
 * same on both targets.  The bitfield sequences are copied verbatim from
 * dlls/wined3d/wined3d_private.h -- bitfield packing is the one place where
 * i386 and AAPCS are documented to be able to differ. */
#define offsetof(t,m) __builtin_offsetof(t,m)


typedef unsigned int DWORD;
typedef int BOOL;
typedef long LONG_;
typedef void *PTR;

/* wined3d_context, bitfield block, verbatim */
struct ctx_bits {
    DWORD last_swizzle_map;
    DWORD shader_update_mask : 6;
    DWORD update_shader_resource_bindings : 1;
    DWORD update_compute_shader_resource_bindings : 1;
    DWORD last_was_rhw : 1;
    DWORD last_was_ffp_blit : 1;
    DWORD last_was_blit : 1;
    DWORD last_was_dual_source_blend : 1;
    DWORD lowest_disabled_stage : 4;
    DWORD fixed_function_usage_map : 8;
    DWORD uses_uavs : 1;
    DWORD uses_fbo_attached_resources : 1;
    DWORD transform_feedback_active : 1;
    DWORD transform_feedback_paused : 1;
    DWORD current : 1;
    DWORD destroyed : 1;
    DWORD destroy_delayed : 1;
    DWORD update_unordered_access_view_bindings : 1;
    DWORD update_compute_unordered_access_view_bindings : 1;
    DWORD update_primitive_type : 1;
    DWORD update_multisample_state : 1;
    DWORD update_patch_vertex_count : 1;
    DWORD padding : 28;
    DWORD clip_distance_mask : 8;
    DWORD constant_update_mask;
    DWORD numbered_array_mask;
    unsigned int viewport_count;
    unsigned int scissor_rect_count;
};

/* ffp_frag_settings tail, verbatim shape */
struct ffp_bits {
    unsigned char op[8][6];
    unsigned int fog;
    unsigned char color_key_enabled : 1;
    unsigned char pointsprite : 1;
    unsigned char flatshading : 1;
    unsigned char alpha_test_func : 3;
    unsigned char padding : 2;
};

/* wined3d_stream_info tail */
struct si_bits {
    PTR elements[16];
    DWORD use_map;
    BOOL position_transformed : 1;
    BOOL all_vbo : 1;
};

/* mixed scalar block: the alignment question, separate from bitfields */
struct mixed {
    unsigned int a;
    PTR p;
    float f[4];
    unsigned long long q;   /* the one 64-bit case found: wined3d_bo_gl.command_fence_id */
    unsigned int b;
};


/* One initialised table, read back with objcopy so the comparison does not
 * depend on the object format. Order must match NAMES in the reader. */
const unsigned int probe_table[] = {
    sizeof(struct ctx_bits), _Alignof(struct ctx_bits),
    offsetof(struct ctx_bits, constant_update_mask),
    offsetof(struct ctx_bits, numbered_array_mask),
    offsetof(struct ctx_bits, viewport_count),
    offsetof(struct ctx_bits, scissor_rect_count),

    sizeof(struct ffp_bits), _Alignof(struct ffp_bits),
    offsetof(struct ffp_bits, fog),

    sizeof(struct si_bits), _Alignof(struct si_bits),
    offsetof(struct si_bits, use_map),

    sizeof(struct mixed), _Alignof(struct mixed),
    offsetof(struct mixed, f), offsetof(struct mixed, q), offsetof(struct mixed, b),
};
