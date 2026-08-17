/* layout-exact, generated from the shipping i386 DWARF -- do not edit */
struct wined3d_fb_state {
    void * render_targets[8];
    void * depth_stencil;
};
_Static_assert(sizeof(struct wined3d_fb_state) == 36, "wined3d_fb_state size");
_Static_assert(__builtin_offsetof(struct wined3d_fb_state, render_targets) == 0, "wined3d_fb_state.render_targets moved");
_Static_assert(__builtin_offsetof(struct wined3d_fb_state, depth_stencil) == 32, "wined3d_fb_state.depth_stencil moved");
struct wined3d_stream_output {
    void * buffer;
    unsigned int offset;
};
_Static_assert(sizeof(struct wined3d_stream_output) == 8, "wined3d_stream_output size");
_Static_assert(__builtin_offsetof(struct wined3d_stream_output, buffer) == 0, "wined3d_stream_output.buffer moved");
_Static_assert(__builtin_offsetof(struct wined3d_stream_output, offset) == 4, "wined3d_stream_output.offset moved");
struct wined3d_stream_state {
    void * buffer;
    unsigned int offset;
    unsigned int stride;
    unsigned int frequency;
    unsigned int flags;
};
_Static_assert(sizeof(struct wined3d_stream_state) == 20, "wined3d_stream_state size");
_Static_assert(__builtin_offsetof(struct wined3d_stream_state, buffer) == 0, "wined3d_stream_state.buffer moved");
_Static_assert(__builtin_offsetof(struct wined3d_stream_state, offset) == 4, "wined3d_stream_state.offset moved");
_Static_assert(__builtin_offsetof(struct wined3d_stream_state, stride) == 8, "wined3d_stream_state.stride moved");
_Static_assert(__builtin_offsetof(struct wined3d_stream_state, frequency) == 12, "wined3d_stream_state.frequency moved");
_Static_assert(__builtin_offsetof(struct wined3d_stream_state, flags) == 16, "wined3d_stream_state.flags moved");
struct wined3d_constant_buffer_state {
    void * buffer;
    unsigned int offset;
    unsigned int size;
};
_Static_assert(sizeof(struct wined3d_constant_buffer_state) == 12, "wined3d_constant_buffer_state size");
_Static_assert(__builtin_offsetof(struct wined3d_constant_buffer_state, buffer) == 0, "wined3d_constant_buffer_state.buffer moved");
_Static_assert(__builtin_offsetof(struct wined3d_constant_buffer_state, offset) == 4, "wined3d_constant_buffer_state.offset moved");
_Static_assert(__builtin_offsetof(struct wined3d_constant_buffer_state, size) == 8, "wined3d_constant_buffer_state.size moved");
struct wined3d_viewport {
    float x;
    float y;
    float width;
    float height;
    float min_z;
    float max_z;
};
_Static_assert(sizeof(struct wined3d_viewport) == 24, "wined3d_viewport size");
_Static_assert(__builtin_offsetof(struct wined3d_viewport, x) == 0, "wined3d_viewport.x moved");
_Static_assert(__builtin_offsetof(struct wined3d_viewport, y) == 4, "wined3d_viewport.y moved");
_Static_assert(__builtin_offsetof(struct wined3d_viewport, width) == 8, "wined3d_viewport.width moved");
_Static_assert(__builtin_offsetof(struct wined3d_viewport, height) == 12, "wined3d_viewport.height moved");
_Static_assert(__builtin_offsetof(struct wined3d_viewport, min_z) == 16, "wined3d_viewport.min_z moved");
_Static_assert(__builtin_offsetof(struct wined3d_viewport, max_z) == 20, "wined3d_viewport.max_z moved");
struct tagRECT {
    int left;
    int top;
    int right;
    int bottom;
};
_Static_assert(sizeof(struct tagRECT) == 16, "tagRECT size");
_Static_assert(__builtin_offsetof(struct tagRECT, left) == 0, "tagRECT.left moved");
_Static_assert(__builtin_offsetof(struct tagRECT, top) == 4, "tagRECT.top moved");
_Static_assert(__builtin_offsetof(struct tagRECT, right) == 8, "tagRECT.right moved");
_Static_assert(__builtin_offsetof(struct tagRECT, bottom) == 12, "tagRECT.bottom moved");
struct rb_tree {
    void * compare;
    void * root;
};
_Static_assert(sizeof(struct rb_tree) == 8, "rb_tree size");
_Static_assert(__builtin_offsetof(struct rb_tree, compare) == 0, "rb_tree.compare moved");
_Static_assert(__builtin_offsetof(struct rb_tree, root) == 4, "rb_tree.root moved");
struct wined3d_light_state {
    struct rb_tree lights_tree;
    void * lights[8];
};
_Static_assert(sizeof(struct wined3d_light_state) == 40, "wined3d_light_state size");
_Static_assert(__builtin_offsetof(struct wined3d_light_state, lights_tree) == 0, "wined3d_light_state.lights_tree moved");
_Static_assert(__builtin_offsetof(struct wined3d_light_state, lights) == 8, "wined3d_light_state.lights moved");
struct wined3d_color {
    float r;
    float g;
    float b;
    float a;
};
_Static_assert(sizeof(struct wined3d_color) == 16, "wined3d_color size");
_Static_assert(__builtin_offsetof(struct wined3d_color, r) == 0, "wined3d_color.r moved");
_Static_assert(__builtin_offsetof(struct wined3d_color, g) == 4, "wined3d_color.g moved");
_Static_assert(__builtin_offsetof(struct wined3d_color, b) == 8, "wined3d_color.b moved");
_Static_assert(__builtin_offsetof(struct wined3d_color, a) == 12, "wined3d_color.a moved");
struct wined3d_extra_vs_args {
    unsigned char clip_planes;
    unsigned char pixel_fog;
    unsigned char flat_shading;
    unsigned char ortho_fog;
};
_Static_assert(sizeof(struct wined3d_extra_vs_args) == 4, "wined3d_extra_vs_args size");
_Static_assert(__builtin_offsetof(struct wined3d_extra_vs_args, clip_planes) == 0, "wined3d_extra_vs_args.clip_planes moved");
_Static_assert(__builtin_offsetof(struct wined3d_extra_vs_args, pixel_fog) == 1, "wined3d_extra_vs_args.pixel_fog moved");
_Static_assert(__builtin_offsetof(struct wined3d_extra_vs_args, flat_shading) == 2, "wined3d_extra_vs_args.flat_shading moved");
_Static_assert(__builtin_offsetof(struct wined3d_extra_vs_args, ortho_fog) == 3, "wined3d_extra_vs_args.ortho_fog moved");
struct wined3d_extra_ps_args {
    unsigned char point_sprite;
    unsigned char flat_shading;
    unsigned char fog_enable;
    unsigned char srgb_write;
    unsigned int fog_mode;
    unsigned int alpha_func;
    unsigned int texcoord_index[8];
    unsigned int texture_transform_flags[4];
};
_Static_assert(sizeof(struct wined3d_extra_ps_args) == 60, "wined3d_extra_ps_args size");
_Static_assert(__builtin_offsetof(struct wined3d_extra_ps_args, point_sprite) == 0, "wined3d_extra_ps_args.point_sprite moved");
_Static_assert(__builtin_offsetof(struct wined3d_extra_ps_args, flat_shading) == 1, "wined3d_extra_ps_args.flat_shading moved");
_Static_assert(__builtin_offsetof(struct wined3d_extra_ps_args, fog_enable) == 2, "wined3d_extra_ps_args.fog_enable moved");
_Static_assert(__builtin_offsetof(struct wined3d_extra_ps_args, srgb_write) == 3, "wined3d_extra_ps_args.srgb_write moved");
_Static_assert(__builtin_offsetof(struct wined3d_extra_ps_args, fog_mode) == 4, "wined3d_extra_ps_args.fog_mode moved");
_Static_assert(__builtin_offsetof(struct wined3d_extra_ps_args, alpha_func) == 8, "wined3d_extra_ps_args.alpha_func moved");
_Static_assert(__builtin_offsetof(struct wined3d_extra_ps_args, texcoord_index) == 12, "wined3d_extra_ps_args.texcoord_index moved");
_Static_assert(__builtin_offsetof(struct wined3d_extra_ps_args, texture_transform_flags) == 44, "wined3d_extra_ps_args.texture_transform_flags moved");
struct wined3d_state {
    unsigned int feature_level;
    unsigned int flags;
    struct wined3d_fb_state fb;
    void * vertex_declaration;
    struct wined3d_stream_output stream_output[4];
    struct wined3d_stream_state streams[16];
    void * index_buffer;
    unsigned int index_format;
    unsigned int index_offset;
    int base_vertex_index;
    int load_base_vertex_index;
    unsigned int primitive_type;
    unsigned int patch_vertex_count;
    void * predicate;
    int predicate_value;
    void * shader[6];
    struct wined3d_constant_buffer_state cb[6][15];
    void * sampler[6][16];
    void * shader_resource_view[6][128];
    void * unordered_access_view[2][8];
    unsigned int texture_states[8][18];
    struct wined3d_viewport viewports[16];
    unsigned int viewport_count;
    struct tagRECT scissor_rects[16];
    unsigned int scissor_rect_count;
    struct wined3d_light_state light_state;
    unsigned int render_states[210];
    void * blend_state;
    struct wined3d_color blend_factor;
    unsigned int sample_mask;
    void * depth_stencil_state;
    unsigned int stencil_ref;
    struct wined3d_extra_vs_args extra_vs_args;
    struct wined3d_extra_ps_args extra_ps_args;
    unsigned char depth_bounds_enable;
    unsigned char _pad7261[3];
    float depth_bounds_min;
    float depth_bounds_max;
    void * rasterizer_state;
};
_Static_assert(sizeof(struct wined3d_state) == 7276, "wined3d_state size");
_Static_assert(__builtin_offsetof(struct wined3d_state, feature_level) == 0, "wined3d_state.feature_level moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, flags) == 4, "wined3d_state.flags moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, fb) == 8, "wined3d_state.fb moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, vertex_declaration) == 44, "wined3d_state.vertex_declaration moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, stream_output) == 48, "wined3d_state.stream_output moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, streams) == 80, "wined3d_state.streams moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, index_buffer) == 400, "wined3d_state.index_buffer moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, index_format) == 404, "wined3d_state.index_format moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, index_offset) == 408, "wined3d_state.index_offset moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, base_vertex_index) == 412, "wined3d_state.base_vertex_index moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, load_base_vertex_index) == 416, "wined3d_state.load_base_vertex_index moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, primitive_type) == 420, "wined3d_state.primitive_type moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, patch_vertex_count) == 424, "wined3d_state.patch_vertex_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, predicate) == 428, "wined3d_state.predicate moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, predicate_value) == 432, "wined3d_state.predicate_value moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, shader) == 436, "wined3d_state.shader moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, cb) == 460, "wined3d_state.cb moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, sampler) == 1540, "wined3d_state.sampler moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, shader_resource_view) == 1924, "wined3d_state.shader_resource_view moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, unordered_access_view) == 4996, "wined3d_state.unordered_access_view moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, texture_states) == 5060, "wined3d_state.texture_states moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, viewports) == 5636, "wined3d_state.viewports moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, viewport_count) == 6020, "wined3d_state.viewport_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, scissor_rects) == 6024, "wined3d_state.scissor_rects moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, scissor_rect_count) == 6280, "wined3d_state.scissor_rect_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, light_state) == 6284, "wined3d_state.light_state moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, render_states) == 6324, "wined3d_state.render_states moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, blend_state) == 7164, "wined3d_state.blend_state moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, blend_factor) == 7168, "wined3d_state.blend_factor moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, sample_mask) == 7184, "wined3d_state.sample_mask moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, depth_stencil_state) == 7188, "wined3d_state.depth_stencil_state moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, stencil_ref) == 7192, "wined3d_state.stencil_ref moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, extra_vs_args) == 7196, "wined3d_state.extra_vs_args moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, extra_ps_args) == 7200, "wined3d_state.extra_ps_args moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, depth_bounds_enable) == 7260, "wined3d_state.depth_bounds_enable moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, depth_bounds_min) == 7264, "wined3d_state.depth_bounds_min moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, depth_bounds_max) == 7268, "wined3d_state.depth_bounds_max moved");
_Static_assert(__builtin_offsetof(struct wined3d_state, rasterizer_state) == 7272, "wined3d_state.rasterizer_state moved");
struct anon_1 {
    void * texture;
    unsigned int sub_resource_idx;
};
_Static_assert(sizeof(struct anon_1) == 8, "anon_1 size");
_Static_assert(__builtin_offsetof(struct anon_1, texture) == 0, "anon_1.texture moved");
_Static_assert(__builtin_offsetof(struct anon_1, sub_resource_idx) == 4, "anon_1.sub_resource_idx moved");
struct wined3d_bo_address {
    void * buffer_object;
    void * addr;
};
_Static_assert(sizeof(struct wined3d_bo_address) == 8, "wined3d_bo_address size");
_Static_assert(__builtin_offsetof(struct wined3d_bo_address, buffer_object) == 0, "wined3d_bo_address.buffer_object moved");
_Static_assert(__builtin_offsetof(struct wined3d_bo_address, addr) == 4, "wined3d_bo_address.addr moved");
struct wined3d_stream_info_element {
    void * format;
    struct wined3d_bo_address data;
    unsigned int stride;
    unsigned int stream_idx;
    unsigned int divisor;
    unsigned char instanced;
    unsigned char _pad25[3];
};
_Static_assert(sizeof(struct wined3d_stream_info_element) == 28, "wined3d_stream_info_element size");
_Static_assert(__builtin_offsetof(struct wined3d_stream_info_element, format) == 0, "wined3d_stream_info_element.format moved");
_Static_assert(__builtin_offsetof(struct wined3d_stream_info_element, data) == 4, "wined3d_stream_info_element.data moved");
_Static_assert(__builtin_offsetof(struct wined3d_stream_info_element, stride) == 12, "wined3d_stream_info_element.stride moved");
_Static_assert(__builtin_offsetof(struct wined3d_stream_info_element, stream_idx) == 16, "wined3d_stream_info_element.stream_idx moved");
_Static_assert(__builtin_offsetof(struct wined3d_stream_info_element, divisor) == 20, "wined3d_stream_info_element.divisor moved");
_Static_assert(__builtin_offsetof(struct wined3d_stream_info_element, instanced) == 24, "wined3d_stream_info_element.instanced moved");
struct wined3d_stream_info {
    struct wined3d_stream_info_element elements[32];
    unsigned int _bits896;
    unsigned int swizzle_map;
    unsigned int use_map;
};
_Static_assert(sizeof(struct wined3d_stream_info) == 908, "wined3d_stream_info size");
_Static_assert(__builtin_offsetof(struct wined3d_stream_info, elements) == 0, "wined3d_stream_info.elements moved");
_Static_assert(__builtin_offsetof(struct wined3d_stream_info, _bits896) == 896, "wined3d_stream_info._bits896 moved");
_Static_assert(__builtin_offsetof(struct wined3d_stream_info, swizzle_map) == 900, "wined3d_stream_info.swizzle_map moved");
_Static_assert(__builtin_offsetof(struct wined3d_stream_info, use_map) == 904, "wined3d_stream_info.use_map moved");
#define wined3d_stream_info_get_position_transformed(p)  ((((p)->_bits896) >> 0) & 0x1u)
#define wined3d_stream_info_set_position_transformed(p,v) ((p)->_bits896 = (((p)->_bits896 & ~(0x1u << 0)) | (((v) & 0x1u) << 0)))
#define wined3d_stream_info_get_all_vbo(p)  ((((p)->_bits896) >> 1) & 0x1u)
#define wined3d_stream_info_set_all_vbo(p,v) ((p)->_bits896 = (((p)->_bits896 & ~(0x1u << 1)) | (((v) & 0x1u) << 1)))
struct wined3d_context {
    void * d3d_info;
    void * state_table;
    unsigned int dirty_graphics_states[12];
    unsigned int dirty_compute_states[1];
    void * device;
    void * swapchain;
    struct anon_1 current_rt;
    unsigned int last_swizzle_map;
    unsigned int _bits80;
    unsigned int _bits84;
    unsigned int _bits88;
    unsigned int constant_update_mask;
    unsigned int numbered_array_mask;
    void * shader_backend_data;
    struct wined3d_stream_info stream_info;
    unsigned int viewport_count;
    unsigned int scissor_rect_count;
};
_Static_assert(sizeof(struct wined3d_context) == 1020, "wined3d_context size");
_Static_assert(__builtin_offsetof(struct wined3d_context, d3d_info) == 0, "wined3d_context.d3d_info moved");
_Static_assert(__builtin_offsetof(struct wined3d_context, state_table) == 4, "wined3d_context.state_table moved");
_Static_assert(__builtin_offsetof(struct wined3d_context, dirty_graphics_states) == 8, "wined3d_context.dirty_graphics_states moved");
_Static_assert(__builtin_offsetof(struct wined3d_context, dirty_compute_states) == 56, "wined3d_context.dirty_compute_states moved");
_Static_assert(__builtin_offsetof(struct wined3d_context, device) == 60, "wined3d_context.device moved");
_Static_assert(__builtin_offsetof(struct wined3d_context, swapchain) == 64, "wined3d_context.swapchain moved");
_Static_assert(__builtin_offsetof(struct wined3d_context, current_rt) == 68, "wined3d_context.current_rt moved");
_Static_assert(__builtin_offsetof(struct wined3d_context, last_swizzle_map) == 76, "wined3d_context.last_swizzle_map moved");
_Static_assert(__builtin_offsetof(struct wined3d_context, _bits80) == 80, "wined3d_context._bits80 moved");
_Static_assert(__builtin_offsetof(struct wined3d_context, _bits84) == 84, "wined3d_context._bits84 moved");
_Static_assert(__builtin_offsetof(struct wined3d_context, _bits88) == 88, "wined3d_context._bits88 moved");
_Static_assert(__builtin_offsetof(struct wined3d_context, constant_update_mask) == 92, "wined3d_context.constant_update_mask moved");
_Static_assert(__builtin_offsetof(struct wined3d_context, numbered_array_mask) == 96, "wined3d_context.numbered_array_mask moved");
_Static_assert(__builtin_offsetof(struct wined3d_context, shader_backend_data) == 100, "wined3d_context.shader_backend_data moved");
_Static_assert(__builtin_offsetof(struct wined3d_context, stream_info) == 104, "wined3d_context.stream_info moved");
_Static_assert(__builtin_offsetof(struct wined3d_context, viewport_count) == 1012, "wined3d_context.viewport_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_context, scissor_rect_count) == 1016, "wined3d_context.scissor_rect_count moved");
#define wined3d_context_get_shader_update_mask(p)  ((((p)->_bits80) >> 0) & 0x3fu)
#define wined3d_context_set_shader_update_mask(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0x3fu << 0)) | (((v) & 0x3fu) << 0)))
#define wined3d_context_get_update_shader_resource_bindings(p)  ((((p)->_bits80) >> 6) & 0x1u)
#define wined3d_context_set_update_shader_resource_bindings(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0x1u << 6)) | (((v) & 0x1u) << 6)))
#define wined3d_context_get_update_compute_shader_resource_bindings(p)  ((((p)->_bits80) >> 7) & 0x1u)
#define wined3d_context_set_update_compute_shader_resource_bindings(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0x1u << 7)) | (((v) & 0x1u) << 7)))
#define wined3d_context_get_last_was_rhw(p)  ((((p)->_bits80) >> 8) & 0x1u)
#define wined3d_context_set_last_was_rhw(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0x1u << 8)) | (((v) & 0x1u) << 8)))
#define wined3d_context_get_last_was_ffp_blit(p)  ((((p)->_bits80) >> 9) & 0x1u)
#define wined3d_context_set_last_was_ffp_blit(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0x1u << 9)) | (((v) & 0x1u) << 9)))
#define wined3d_context_get_last_was_blit(p)  ((((p)->_bits80) >> 10) & 0x1u)
#define wined3d_context_set_last_was_blit(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0x1u << 10)) | (((v) & 0x1u) << 10)))
#define wined3d_context_get_last_was_dual_source_blend(p)  ((((p)->_bits80) >> 11) & 0x1u)
#define wined3d_context_set_last_was_dual_source_blend(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0x1u << 11)) | (((v) & 0x1u) << 11)))
#define wined3d_context_get_lowest_disabled_stage(p)  ((((p)->_bits80) >> 12) & 0xfu)
#define wined3d_context_set_lowest_disabled_stage(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0xfu << 12)) | (((v) & 0xfu) << 12)))
#define wined3d_context_get_fixed_function_usage_map(p)  ((((p)->_bits80) >> 16) & 0xffu)
#define wined3d_context_set_fixed_function_usage_map(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0xffu << 16)) | (((v) & 0xffu) << 16)))
#define wined3d_context_get_uses_uavs(p)  ((((p)->_bits80) >> 24) & 0x1u)
#define wined3d_context_set_uses_uavs(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0x1u << 24)) | (((v) & 0x1u) << 24)))
#define wined3d_context_get_uses_fbo_attached_resources(p)  ((((p)->_bits80) >> 25) & 0x1u)
#define wined3d_context_set_uses_fbo_attached_resources(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0x1u << 25)) | (((v) & 0x1u) << 25)))
#define wined3d_context_get_transform_feedback_active(p)  ((((p)->_bits80) >> 26) & 0x1u)
#define wined3d_context_set_transform_feedback_active(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0x1u << 26)) | (((v) & 0x1u) << 26)))
#define wined3d_context_get_transform_feedback_paused(p)  ((((p)->_bits80) >> 27) & 0x1u)
#define wined3d_context_set_transform_feedback_paused(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0x1u << 27)) | (((v) & 0x1u) << 27)))
#define wined3d_context_get_current(p)  ((((p)->_bits80) >> 28) & 0x1u)
#define wined3d_context_set_current(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0x1u << 28)) | (((v) & 0x1u) << 28)))
#define wined3d_context_get_destroyed(p)  ((((p)->_bits80) >> 29) & 0x1u)
#define wined3d_context_set_destroyed(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0x1u << 29)) | (((v) & 0x1u) << 29)))
#define wined3d_context_get_destroy_delayed(p)  ((((p)->_bits80) >> 30) & 0x1u)
#define wined3d_context_set_destroy_delayed(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0x1u << 30)) | (((v) & 0x1u) << 30)))
#define wined3d_context_get_update_unordered_access_view_bindings(p)  ((((p)->_bits80) >> 31) & 0x1u)
#define wined3d_context_set_update_unordered_access_view_bindings(p,v) ((p)->_bits80 = (((p)->_bits80 & ~(0x1u << 31)) | (((v) & 0x1u) << 31)))
#define wined3d_context_get_update_compute_unordered_access_view_bindings(p)  ((((p)->_bits84) >> 0) & 0x1u)
#define wined3d_context_set_update_compute_unordered_access_view_bindings(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 0)) | (((v) & 0x1u) << 0)))
#define wined3d_context_get_update_primitive_type(p)  ((((p)->_bits84) >> 1) & 0x1u)
#define wined3d_context_set_update_primitive_type(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 1)) | (((v) & 0x1u) << 1)))
#define wined3d_context_get_update_multisample_state(p)  ((((p)->_bits84) >> 2) & 0x1u)
#define wined3d_context_set_update_multisample_state(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 2)) | (((v) & 0x1u) << 2)))
#define wined3d_context_get_update_patch_vertex_count(p)  ((((p)->_bits84) >> 3) & 0x1u)
#define wined3d_context_set_update_patch_vertex_count(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 3)) | (((v) & 0x1u) << 3)))
#define wined3d_context_get_padding(p)  ((((p)->_bits84) >> 4) & 0xfffffffu)
#define wined3d_context_set_padding(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0xfffffffu << 4)) | (((v) & 0xfffffffu) << 4)))
#define wined3d_context_get_clip_distance_mask(p)  ((((p)->_bits88) >> 0) & 0xffu)
#define wined3d_context_set_clip_distance_mask(p,v) ((p)->_bits88 = (((p)->_bits88 & ~(0xffu << 0)) | (((v) & 0xffu) << 0)))
struct wined3d_state_entry {
    unsigned int representative;
    void * apply;
};
_Static_assert(sizeof(struct wined3d_state_entry) == 8, "wined3d_state_entry size");
_Static_assert(__builtin_offsetof(struct wined3d_state_entry, representative) == 0, "wined3d_state_entry.representative moved");
_Static_assert(__builtin_offsetof(struct wined3d_state_entry, apply) == 4, "wined3d_state_entry.apply moved");
struct wined3d_device_creation_parameters {
    unsigned int adapter_idx;
    unsigned int device_type;
    void * focus_window;
    unsigned int flags;
};
_Static_assert(sizeof(struct wined3d_device_creation_parameters) == 16, "wined3d_device_creation_parameters size");
_Static_assert(__builtin_offsetof(struct wined3d_device_creation_parameters, adapter_idx) == 0, "wined3d_device_creation_parameters.adapter_idx moved");
_Static_assert(__builtin_offsetof(struct wined3d_device_creation_parameters, device_type) == 4, "wined3d_device_creation_parameters.device_type moved");
_Static_assert(__builtin_offsetof(struct wined3d_device_creation_parameters, focus_window) == 8, "wined3d_device_creation_parameters.focus_window moved");
_Static_assert(__builtin_offsetof(struct wined3d_device_creation_parameters, flags) == 12, "wined3d_device_creation_parameters.flags moved");
struct list {
    void * next;
    void * prev;
};
_Static_assert(sizeof(struct list) == 8, "list size");
_Static_assert(__builtin_offsetof(struct list, next) == 0, "list.next moved");
_Static_assert(__builtin_offsetof(struct list, prev) == 4, "list.prev moved");
struct _RTL_CRITICAL_SECTION {
    void * DebugInfo;
    int LockCount;
    int RecursionCount;
    void * OwningThread;
    void * LockSemaphore;
    unsigned int SpinCount;
};
_Static_assert(sizeof(struct _RTL_CRITICAL_SECTION) == 24, "_RTL_CRITICAL_SECTION size");
_Static_assert(__builtin_offsetof(struct _RTL_CRITICAL_SECTION, DebugInfo) == 0, "_RTL_CRITICAL_SECTION.DebugInfo moved");
_Static_assert(__builtin_offsetof(struct _RTL_CRITICAL_SECTION, LockCount) == 4, "_RTL_CRITICAL_SECTION.LockCount moved");
_Static_assert(__builtin_offsetof(struct _RTL_CRITICAL_SECTION, RecursionCount) == 8, "_RTL_CRITICAL_SECTION.RecursionCount moved");
_Static_assert(__builtin_offsetof(struct _RTL_CRITICAL_SECTION, OwningThread) == 12, "_RTL_CRITICAL_SECTION.OwningThread moved");
_Static_assert(__builtin_offsetof(struct _RTL_CRITICAL_SECTION, LockSemaphore) == 16, "_RTL_CRITICAL_SECTION.LockSemaphore moved");
_Static_assert(__builtin_offsetof(struct _RTL_CRITICAL_SECTION, SpinCount) == 20, "_RTL_CRITICAL_SECTION.SpinCount moved");
struct wined3d_device {
    int ref;
    void * device_parent;
    void * wined3d;
    void * adapter;
    void * shader_backend;
    void * shader_priv;
    void * fragment_priv;
    void * vertex_priv;
    struct wined3d_state_entry state_table[385];
    void * multistate_funcs[385];
    void * blitter;
    unsigned char _bits4656;
    unsigned char surface_alignment;
    unsigned short _bits4658;
    struct wined3d_device_creation_parameters create_parms;
    void * focus_window;
    void * back_buffer_view;
    void * swapchains;
    unsigned int swapchain_count;
    unsigned int max_frame_latency;
    struct list resources;
    struct list shaders;
    struct rb_tree so_descs;
    struct rb_tree samplers;
    struct rb_tree rasterizer_states;
    struct rb_tree blend_states;
    struct rb_tree depth_stencil_states;
    struct rb_tree ffp_vertex_shaders;
    struct rb_tree ffp_pixel_shaders;
    void * auto_depth_stencil_view;
    unsigned int xHotSpot;
    unsigned int yHotSpot;
    unsigned int xScreenSpace;
    unsigned int yScreenSpace;
    unsigned int cursorWidth;
    unsigned int cursorHeight;
    void * cursor_texture;
    void * hardwareCursor;
    void * logo_texture;
    void * default_sampler;
    void * null_sampler;
    void * cs;
    void * push_constants[8];
    void * contexts;
    unsigned int context_count;
    struct _RTL_CRITICAL_SECTION bo_map_lock;
};
_Static_assert(sizeof(struct wined3d_device) == 4884, "wined3d_device size");
_Static_assert(__builtin_offsetof(struct wined3d_device, ref) == 0, "wined3d_device.ref moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, device_parent) == 4, "wined3d_device.device_parent moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, wined3d) == 8, "wined3d_device.wined3d moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, adapter) == 12, "wined3d_device.adapter moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, shader_backend) == 16, "wined3d_device.shader_backend moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, shader_priv) == 20, "wined3d_device.shader_priv moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, fragment_priv) == 24, "wined3d_device.fragment_priv moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, vertex_priv) == 28, "wined3d_device.vertex_priv moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, state_table) == 32, "wined3d_device.state_table moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, multistate_funcs) == 3112, "wined3d_device.multistate_funcs moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, blitter) == 4652, "wined3d_device.blitter moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, _bits4656) == 4656, "wined3d_device._bits4656 moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, surface_alignment) == 4657, "wined3d_device.surface_alignment moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, _bits4658) == 4658, "wined3d_device._bits4658 moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, create_parms) == 4660, "wined3d_device.create_parms moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, focus_window) == 4676, "wined3d_device.focus_window moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, back_buffer_view) == 4680, "wined3d_device.back_buffer_view moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, swapchains) == 4684, "wined3d_device.swapchains moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, swapchain_count) == 4688, "wined3d_device.swapchain_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, max_frame_latency) == 4692, "wined3d_device.max_frame_latency moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, resources) == 4696, "wined3d_device.resources moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, shaders) == 4704, "wined3d_device.shaders moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, so_descs) == 4712, "wined3d_device.so_descs moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, samplers) == 4720, "wined3d_device.samplers moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, rasterizer_states) == 4728, "wined3d_device.rasterizer_states moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, blend_states) == 4736, "wined3d_device.blend_states moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, depth_stencil_states) == 4744, "wined3d_device.depth_stencil_states moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, ffp_vertex_shaders) == 4752, "wined3d_device.ffp_vertex_shaders moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, ffp_pixel_shaders) == 4760, "wined3d_device.ffp_pixel_shaders moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, auto_depth_stencil_view) == 4768, "wined3d_device.auto_depth_stencil_view moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, xHotSpot) == 4772, "wined3d_device.xHotSpot moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, yHotSpot) == 4776, "wined3d_device.yHotSpot moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, xScreenSpace) == 4780, "wined3d_device.xScreenSpace moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, yScreenSpace) == 4784, "wined3d_device.yScreenSpace moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, cursorWidth) == 4788, "wined3d_device.cursorWidth moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, cursorHeight) == 4792, "wined3d_device.cursorHeight moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, cursor_texture) == 4796, "wined3d_device.cursor_texture moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, hardwareCursor) == 4800, "wined3d_device.hardwareCursor moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, logo_texture) == 4804, "wined3d_device.logo_texture moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, default_sampler) == 4808, "wined3d_device.default_sampler moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, null_sampler) == 4812, "wined3d_device.null_sampler moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, cs) == 4816, "wined3d_device.cs moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, push_constants) == 4820, "wined3d_device.push_constants moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, contexts) == 4852, "wined3d_device.contexts moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, context_count) == 4856, "wined3d_device.context_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_device, bo_map_lock) == 4860, "wined3d_device.bo_map_lock moved");
#define wined3d_device_get_bCursorVisible(p)  ((((p)->_bits4656) >> 0) & 0x1u)
#define wined3d_device_set_bCursorVisible(p,v) ((p)->_bits4656 = (((p)->_bits4656 & ~(0x1u << 0)) | (((v) & 0x1u) << 0)))
#define wined3d_device_get_d3d_initialized(p)  ((((p)->_bits4656) >> 1) & 0x1u)
#define wined3d_device_set_d3d_initialized(p,v) ((p)->_bits4656 = (((p)->_bits4656 & ~(0x1u << 1)) | (((v) & 0x1u) << 1)))
#define wined3d_device_get_inScene(p)  ((((p)->_bits4656) >> 2) & 0x1u)
#define wined3d_device_set_inScene(p,v) ((p)->_bits4656 = (((p)->_bits4656 & ~(0x1u << 2)) | (((v) & 0x1u) << 2)))
#define wined3d_device_get_softwareVertexProcessing(p)  ((((p)->_bits4656) >> 3) & 0x1u)
#define wined3d_device_set_softwareVertexProcessing(p,v) ((p)->_bits4656 = (((p)->_bits4656 & ~(0x1u << 3)) | (((v) & 0x1u) << 3)))
#define wined3d_device_get_restore_screensaver(p)  ((((p)->_bits4656) >> 4) & 0x1u)
#define wined3d_device_set_restore_screensaver(p,v) ((p)->_bits4656 = (((p)->_bits4656 & ~(0x1u << 4)) | (((v) & 0x1u) << 4)))
#define wined3d_device_get_padding(p)  ((((p)->_bits4656) >> 5) & 0x7u)
#define wined3d_device_set_padding(p,v) ((p)->_bits4656 = (((p)->_bits4656 & ~(0x7u << 5)) | (((v) & 0x7u) << 5)))
#define wined3d_device_get_padding2(p)  ((((p)->_bits4658) >> 0) & 0xffffu)
#define wined3d_device_set_padding2(p,v) ((p)->_bits4658 = (((p)->_bits4658 & ~(0xffffu << 0)) | (((v) & 0xffffu) << 0)))
struct wined3d_const_bo_address {
    void * buffer_object;
    void * addr;
};
_Static_assert(sizeof(struct wined3d_const_bo_address) == 8, "wined3d_const_bo_address size");
_Static_assert(__builtin_offsetof(struct wined3d_const_bo_address, buffer_object) == 0, "wined3d_const_bo_address.buffer_object moved");
_Static_assert(__builtin_offsetof(struct wined3d_const_bo_address, addr) == 4, "wined3d_const_bo_address.addr moved");
struct upload_bo {
    struct wined3d_const_bo_address addr;
    unsigned int flags;
};
_Static_assert(sizeof(struct upload_bo) == 12, "upload_bo size");
_Static_assert(__builtin_offsetof(struct upload_bo, addr) == 0, "upload_bo.addr moved");
_Static_assert(__builtin_offsetof(struct upload_bo, flags) == 8, "upload_bo.flags moved");
struct wined3d_box {
    unsigned int left;
    unsigned int top;
    unsigned int right;
    unsigned int bottom;
    unsigned int front;
    unsigned int back;
};
_Static_assert(sizeof(struct wined3d_box) == 24, "wined3d_box size");
_Static_assert(__builtin_offsetof(struct wined3d_box, left) == 0, "wined3d_box.left moved");
_Static_assert(__builtin_offsetof(struct wined3d_box, top) == 4, "wined3d_box.top moved");
_Static_assert(__builtin_offsetof(struct wined3d_box, right) == 8, "wined3d_box.right moved");
_Static_assert(__builtin_offsetof(struct wined3d_box, bottom) == 12, "wined3d_box.bottom moved");
_Static_assert(__builtin_offsetof(struct wined3d_box, front) == 16, "wined3d_box.front moved");
_Static_assert(__builtin_offsetof(struct wined3d_box, back) == 20, "wined3d_box.back moved");
struct wined3d_client_resource {
    struct wined3d_bo_address addr;
    struct upload_bo mapped_upload;
    struct wined3d_box mapped_box;
};
_Static_assert(sizeof(struct wined3d_client_resource) == 44, "wined3d_client_resource size");
_Static_assert(__builtin_offsetof(struct wined3d_client_resource, addr) == 0, "wined3d_client_resource.addr moved");
_Static_assert(__builtin_offsetof(struct wined3d_client_resource, mapped_upload) == 8, "wined3d_client_resource.mapped_upload moved");
_Static_assert(__builtin_offsetof(struct wined3d_client_resource, mapped_box) == 20, "wined3d_client_resource.mapped_box moved");
struct wined3d_resource {
    int ref;
    int bind_count;
    int map_count;
    unsigned int access_time;
    void * device;
    unsigned int type;
    unsigned int gl_type;
    void * format;
    unsigned int format_attrs;
    unsigned int format_caps;
    unsigned int multisample_type;
    unsigned int multisample_quality;
    unsigned int usage;
    unsigned int bind_flags;
    unsigned int access;
    unsigned short draw_binding;
    unsigned short map_binding;
    unsigned int width;
    unsigned int height;
    unsigned int depth;
    unsigned int size;
    unsigned int priority;
    void * heap_pointer;
    void * heap_memory;
    unsigned int _bits92;
    struct wined3d_client_resource client;
    void * parent;
    void * parent_ops;
    void * resource_ops;
    struct list resource_list_entry;
    int srv_bind_count_device;
    int rtv_bind_count_device;
};
_Static_assert(sizeof(struct wined3d_resource) == 168, "wined3d_resource size");
_Static_assert(__builtin_offsetof(struct wined3d_resource, ref) == 0, "wined3d_resource.ref moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, bind_count) == 4, "wined3d_resource.bind_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, map_count) == 8, "wined3d_resource.map_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, access_time) == 12, "wined3d_resource.access_time moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, device) == 16, "wined3d_resource.device moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, type) == 20, "wined3d_resource.type moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, gl_type) == 24, "wined3d_resource.gl_type moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, format) == 28, "wined3d_resource.format moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, format_attrs) == 32, "wined3d_resource.format_attrs moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, format_caps) == 36, "wined3d_resource.format_caps moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, multisample_type) == 40, "wined3d_resource.multisample_type moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, multisample_quality) == 44, "wined3d_resource.multisample_quality moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, usage) == 48, "wined3d_resource.usage moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, bind_flags) == 52, "wined3d_resource.bind_flags moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, access) == 56, "wined3d_resource.access moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, draw_binding) == 60, "wined3d_resource.draw_binding moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, map_binding) == 62, "wined3d_resource.map_binding moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, width) == 64, "wined3d_resource.width moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, height) == 68, "wined3d_resource.height moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, depth) == 72, "wined3d_resource.depth moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, size) == 76, "wined3d_resource.size moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, priority) == 80, "wined3d_resource.priority moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, heap_pointer) == 84, "wined3d_resource.heap_pointer moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, heap_memory) == 88, "wined3d_resource.heap_memory moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, _bits92) == 92, "wined3d_resource._bits92 moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, client) == 96, "wined3d_resource.client moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, parent) == 140, "wined3d_resource.parent moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, parent_ops) == 144, "wined3d_resource.parent_ops moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, resource_ops) == 148, "wined3d_resource.resource_ops moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, resource_list_entry) == 152, "wined3d_resource.resource_list_entry moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, srv_bind_count_device) == 160, "wined3d_resource.srv_bind_count_device moved");
_Static_assert(__builtin_offsetof(struct wined3d_resource, rtv_bind_count_device) == 164, "wined3d_resource.rtv_bind_count_device moved");
#define wined3d_resource_get_pin_sysmem(p)  ((((p)->_bits92) >> 0) & 0x1u)
#define wined3d_resource_set_pin_sysmem(p,v) ((p)->_bits92 = (((p)->_bits92 & ~(0x1u << 0)) | (((v) & 0x1u) << 0)))
struct wined3d_bo_user {
    struct list entry;
    unsigned char valid;
    unsigned char _pad9[3];
};
_Static_assert(sizeof(struct wined3d_bo_user) == 12, "wined3d_bo_user size");
_Static_assert(__builtin_offsetof(struct wined3d_bo_user, entry) == 0, "wined3d_bo_user.entry moved");
_Static_assert(__builtin_offsetof(struct wined3d_bo_user, valid) == 8, "wined3d_bo_user.valid moved");
struct wined3d_buffer {
    struct wined3d_resource resource;
    void * buffer_ops;
    unsigned int structure_byte_stride;
    unsigned int flags;
    unsigned int locations;
    void * map_ptr;
    void * buffer_object;
    struct wined3d_bo_user bo_user;
    void * dirty_ranges;
    unsigned int dirty_range_count;
    unsigned int dirty_ranges_capacity;
};
_Static_assert(sizeof(struct wined3d_buffer) == 216, "wined3d_buffer size");
_Static_assert(__builtin_offsetof(struct wined3d_buffer, resource) == 0, "wined3d_buffer.resource moved");
_Static_assert(__builtin_offsetof(struct wined3d_buffer, buffer_ops) == 168, "wined3d_buffer.buffer_ops moved");
_Static_assert(__builtin_offsetof(struct wined3d_buffer, structure_byte_stride) == 172, "wined3d_buffer.structure_byte_stride moved");
_Static_assert(__builtin_offsetof(struct wined3d_buffer, flags) == 176, "wined3d_buffer.flags moved");
_Static_assert(__builtin_offsetof(struct wined3d_buffer, locations) == 180, "wined3d_buffer.locations moved");
_Static_assert(__builtin_offsetof(struct wined3d_buffer, map_ptr) == 184, "wined3d_buffer.map_ptr moved");
_Static_assert(__builtin_offsetof(struct wined3d_buffer, buffer_object) == 188, "wined3d_buffer.buffer_object moved");
_Static_assert(__builtin_offsetof(struct wined3d_buffer, bo_user) == 192, "wined3d_buffer.bo_user moved");
_Static_assert(__builtin_offsetof(struct wined3d_buffer, dirty_ranges) == 204, "wined3d_buffer.dirty_ranges moved");
_Static_assert(__builtin_offsetof(struct wined3d_buffer, dirty_range_count) == 208, "wined3d_buffer.dirty_range_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_buffer, dirty_ranges_capacity) == 212, "wined3d_buffer.dirty_ranges_capacity moved");
struct wined3d_color_key {
    unsigned int color_space_low_value;
    unsigned int color_space_high_value;
};
_Static_assert(sizeof(struct wined3d_color_key) == 8, "wined3d_color_key size");
_Static_assert(__builtin_offsetof(struct wined3d_color_key, color_space_low_value) == 0, "wined3d_color_key.color_space_low_value moved");
_Static_assert(__builtin_offsetof(struct wined3d_color_key, color_space_high_value) == 4, "wined3d_color_key.color_space_high_value moved");
struct wined3d_texture_async {
    unsigned int flags;
    struct wined3d_color_key dst_blt_color_key;
    struct wined3d_color_key src_blt_color_key;
    struct wined3d_color_key dst_overlay_color_key;
    struct wined3d_color_key src_overlay_color_key;
    struct wined3d_color_key gl_color_key;
    unsigned int color_key_flags;
};
_Static_assert(sizeof(struct wined3d_texture_async) == 48, "wined3d_texture_async size");
_Static_assert(__builtin_offsetof(struct wined3d_texture_async, flags) == 0, "wined3d_texture_async.flags moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture_async, dst_blt_color_key) == 4, "wined3d_texture_async.dst_blt_color_key moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture_async, src_blt_color_key) == 12, "wined3d_texture_async.src_blt_color_key moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture_async, dst_overlay_color_key) == 20, "wined3d_texture_async.dst_overlay_color_key moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture_async, src_overlay_color_key) == 28, "wined3d_texture_async.src_overlay_color_key moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture_async, gl_color_key) == 36, "wined3d_texture_async.gl_color_key moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture_async, color_key_flags) == 44, "wined3d_texture_async.color_key_flags moved");
struct wined3d_texture {
    struct wined3d_resource resource;
    void * texture_ops;
    void * swapchain;
    unsigned int layer_count;
    unsigned int level_count;
    unsigned int download_count;
    unsigned int sysmem_count;
    unsigned int lod;
    unsigned int flags;
    unsigned int update_map_binding;
    unsigned int row_pitch;
    unsigned int slice_pitch;
    void * identity_srv;
    struct wined3d_texture_async async;
    struct wined3d_color_key src_blt_color_key;
    unsigned int color_key_flags;
    void * dirty_regions;
    void * overlay_info;
    void * dc_info;
    void * sub_resources;
};
_Static_assert(sizeof(struct wined3d_texture) == 292, "wined3d_texture size");
_Static_assert(__builtin_offsetof(struct wined3d_texture, resource) == 0, "wined3d_texture.resource moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, texture_ops) == 168, "wined3d_texture.texture_ops moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, swapchain) == 172, "wined3d_texture.swapchain moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, layer_count) == 176, "wined3d_texture.layer_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, level_count) == 180, "wined3d_texture.level_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, download_count) == 184, "wined3d_texture.download_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, sysmem_count) == 188, "wined3d_texture.sysmem_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, lod) == 192, "wined3d_texture.lod moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, flags) == 196, "wined3d_texture.flags moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, update_map_binding) == 200, "wined3d_texture.update_map_binding moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, row_pitch) == 204, "wined3d_texture.row_pitch moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, slice_pitch) == 208, "wined3d_texture.slice_pitch moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, identity_srv) == 212, "wined3d_texture.identity_srv moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, async) == 216, "wined3d_texture.async moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, src_blt_color_key) == 264, "wined3d_texture.src_blt_color_key moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, color_key_flags) == 272, "wined3d_texture.color_key_flags moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, dirty_regions) == 276, "wined3d_texture.dirty_regions moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, overlay_info) == 280, "wined3d_texture.overlay_info moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, dc_info) == 284, "wined3d_texture.dc_info moved");
_Static_assert(__builtin_offsetof(struct wined3d_texture, sub_resources) == 288, "wined3d_texture.sub_resources moved");
struct color_fixup_desc {
    unsigned short _bits0;
};
_Static_assert(sizeof(struct color_fixup_desc) == 2, "color_fixup_desc size");
_Static_assert(__builtin_offsetof(struct color_fixup_desc, _bits0) == 0, "color_fixup_desc._bits0 moved");
#define color_fixup_desc_get_x_sign_fixup(p)  ((((p)->_bits0) >> 0) & 0x1u)
#define color_fixup_desc_set_x_sign_fixup(p,v) ((p)->_bits0 = (((p)->_bits0 & ~(0x1u << 0)) | (((v) & 0x1u) << 0)))
#define color_fixup_desc_get_x_source(p)  ((((p)->_bits0) >> 1) & 0x7u)
#define color_fixup_desc_set_x_source(p,v) ((p)->_bits0 = (((p)->_bits0 & ~(0x7u << 1)) | (((v) & 0x7u) << 1)))
#define color_fixup_desc_get_y_sign_fixup(p)  ((((p)->_bits0) >> 4) & 0x1u)
#define color_fixup_desc_set_y_sign_fixup(p,v) ((p)->_bits0 = (((p)->_bits0 & ~(0x1u << 4)) | (((v) & 0x1u) << 4)))
#define color_fixup_desc_get_y_source(p)  ((((p)->_bits0) >> 5) & 0x7u)
#define color_fixup_desc_set_y_source(p,v) ((p)->_bits0 = (((p)->_bits0 & ~(0x7u << 5)) | (((v) & 0x7u) << 5)))
#define color_fixup_desc_get_z_sign_fixup(p)  ((((p)->_bits0) >> 8) & 0x1u)
#define color_fixup_desc_set_z_sign_fixup(p,v) ((p)->_bits0 = (((p)->_bits0 & ~(0x1u << 8)) | (((v) & 0x1u) << 8)))
#define color_fixup_desc_get_z_source(p)  ((((p)->_bits0) >> 9) & 0x7u)
#define color_fixup_desc_set_z_source(p,v) ((p)->_bits0 = (((p)->_bits0 & ~(0x7u << 9)) | (((v) & 0x7u) << 9)))
#define color_fixup_desc_get_w_sign_fixup(p)  ((((p)->_bits0) >> 12) & 0x1u)
#define color_fixup_desc_set_w_sign_fixup(p,v) ((p)->_bits0 = (((p)->_bits0 & ~(0x1u << 12)) | (((v) & 0x1u) << 12)))
#define color_fixup_desc_get_w_source(p)  ((((p)->_bits0) >> 13) & 0x7u)
#define color_fixup_desc_set_w_source(p,v) ((p)->_bits0 = (((p)->_bits0 & ~(0x7u << 13)) | (((v) & 0x7u) << 13)))
struct texture_stage_op {
    unsigned int _bits0;
    unsigned int _bits4;
    struct color_fixup_desc color_fixup;
    unsigned char _pad10[2];
    unsigned int _bits12;
};
_Static_assert(sizeof(struct texture_stage_op) == 16, "texture_stage_op size");
_Static_assert(__builtin_offsetof(struct texture_stage_op, _bits0) == 0, "texture_stage_op._bits0 moved");
_Static_assert(__builtin_offsetof(struct texture_stage_op, _bits4) == 4, "texture_stage_op._bits4 moved");
_Static_assert(__builtin_offsetof(struct texture_stage_op, color_fixup) == 8, "texture_stage_op.color_fixup moved");
_Static_assert(__builtin_offsetof(struct texture_stage_op, _bits12) == 12, "texture_stage_op._bits12 moved");
#define texture_stage_op_get_cop(p)  ((((p)->_bits0) >> 0) & 0xffu)
#define texture_stage_op_set_cop(p,v) ((p)->_bits0 = (((p)->_bits0 & ~(0xffu << 0)) | (((v) & 0xffu) << 0)))
#define texture_stage_op_get_carg1(p)  ((((p)->_bits0) >> 8) & 0xffu)
#define texture_stage_op_set_carg1(p,v) ((p)->_bits0 = (((p)->_bits0 & ~(0xffu << 8)) | (((v) & 0xffu) << 8)))
#define texture_stage_op_get_carg2(p)  ((((p)->_bits0) >> 16) & 0xffu)
#define texture_stage_op_set_carg2(p,v) ((p)->_bits0 = (((p)->_bits0 & ~(0xffu << 16)) | (((v) & 0xffu) << 16)))
#define texture_stage_op_get_carg0(p)  ((((p)->_bits0) >> 24) & 0xffu)
#define texture_stage_op_set_carg0(p,v) ((p)->_bits0 = (((p)->_bits0 & ~(0xffu << 24)) | (((v) & 0xffu) << 24)))
#define texture_stage_op_get_aop(p)  ((((p)->_bits4) >> 0) & 0xffu)
#define texture_stage_op_set_aop(p,v) ((p)->_bits4 = (((p)->_bits4 & ~(0xffu << 0)) | (((v) & 0xffu) << 0)))
#define texture_stage_op_get_aarg1(p)  ((((p)->_bits4) >> 8) & 0xffu)
#define texture_stage_op_set_aarg1(p,v) ((p)->_bits4 = (((p)->_bits4 & ~(0xffu << 8)) | (((v) & 0xffu) << 8)))
#define texture_stage_op_get_aarg2(p)  ((((p)->_bits4) >> 16) & 0xffu)
#define texture_stage_op_set_aarg2(p,v) ((p)->_bits4 = (((p)->_bits4 & ~(0xffu << 16)) | (((v) & 0xffu) << 16)))
#define texture_stage_op_get_aarg0(p)  ((((p)->_bits4) >> 24) & 0xffu)
#define texture_stage_op_set_aarg0(p,v) ((p)->_bits4 = (((p)->_bits4 & ~(0xffu << 24)) | (((v) & 0xffu) << 24)))
#define texture_stage_op_get_tex_type(p)  ((((p)->_bits12) >> 0) & 0x7u)
#define texture_stage_op_set_tex_type(p,v) ((p)->_bits12 = (((p)->_bits12 & ~(0x7u << 0)) | (((v) & 0x7u) << 0)))
#define texture_stage_op_get_tmp_dst(p)  ((((p)->_bits12) >> 3) & 0x1u)
#define texture_stage_op_set_tmp_dst(p,v) ((p)->_bits12 = (((p)->_bits12 & ~(0x1u << 3)) | (((v) & 0x1u) << 3)))
#define texture_stage_op_get_projected(p)  ((((p)->_bits12) >> 4) & 0x1u)
#define texture_stage_op_set_projected(p,v) ((p)->_bits12 = (((p)->_bits12 & ~(0x1u << 4)) | (((v) & 0x1u) << 4)))
#define texture_stage_op_get_padding(p)  ((((p)->_bits12) >> 5) & 0x7ffu)
#define texture_stage_op_set_padding(p,v) ((p)->_bits12 = (((p)->_bits12 & ~(0x7ffu << 5)) | (((v) & 0x7ffu) << 5)))
struct ffp_frag_settings {
    struct texture_stage_op op[8];
    unsigned char fog;
    unsigned char sRGB_write;
    unsigned char texcoords_initialized;
    unsigned char _bits131;
};
_Static_assert(sizeof(struct ffp_frag_settings) == 132, "ffp_frag_settings size");
_Static_assert(__builtin_offsetof(struct ffp_frag_settings, op) == 0, "ffp_frag_settings.op moved");
_Static_assert(__builtin_offsetof(struct ffp_frag_settings, fog) == 128, "ffp_frag_settings.fog moved");
_Static_assert(__builtin_offsetof(struct ffp_frag_settings, sRGB_write) == 129, "ffp_frag_settings.sRGB_write moved");
_Static_assert(__builtin_offsetof(struct ffp_frag_settings, texcoords_initialized) == 130, "ffp_frag_settings.texcoords_initialized moved");
_Static_assert(__builtin_offsetof(struct ffp_frag_settings, _bits131) == 131, "ffp_frag_settings._bits131 moved");
#define ffp_frag_settings_get_color_key_enabled(p)  ((((p)->_bits131) >> 0) & 0x1u)
#define ffp_frag_settings_set_color_key_enabled(p,v) ((p)->_bits131 = (((p)->_bits131 & ~(0x1u << 0)) | (((v) & 0x1u) << 0)))
#define ffp_frag_settings_get_pointsprite(p)  ((((p)->_bits131) >> 1) & 0x1u)
#define ffp_frag_settings_set_pointsprite(p,v) ((p)->_bits131 = (((p)->_bits131 & ~(0x1u << 1)) | (((v) & 0x1u) << 1)))
#define ffp_frag_settings_get_flatshading(p)  ((((p)->_bits131) >> 2) & 0x1u)
#define ffp_frag_settings_set_flatshading(p,v) ((p)->_bits131 = (((p)->_bits131 & ~(0x1u << 2)) | (((v) & 0x1u) << 2)))
#define ffp_frag_settings_get_alpha_test_func(p)  ((((p)->_bits131) >> 3) & 0x7u)
#define ffp_frag_settings_set_alpha_test_func(p,v) ((p)->_bits131 = (((p)->_bits131 & ~(0x7u << 3)) | (((v) & 0x7u) << 3)))
#define ffp_frag_settings_get_padding(p)  ((((p)->_bits131) >> 6) & 0x3u)
#define ffp_frag_settings_set_padding(p,v) ((p)->_bits131 = (((p)->_bits131 & ~(0x3u << 6)) | (((v) & 0x3u) << 6)))
struct fragment_caps {
    unsigned int PrimitiveMiscCaps;
    unsigned int TextureOpCaps;
    unsigned int max_blend_stages;
    unsigned int max_textures;
};
_Static_assert(sizeof(struct fragment_caps) == 16, "fragment_caps size");
_Static_assert(__builtin_offsetof(struct fragment_caps, PrimitiveMiscCaps) == 0, "fragment_caps.PrimitiveMiscCaps moved");
_Static_assert(__builtin_offsetof(struct fragment_caps, TextureOpCaps) == 4, "fragment_caps.TextureOpCaps moved");
_Static_assert(__builtin_offsetof(struct fragment_caps, max_blend_stages) == 8, "fragment_caps.max_blend_stages moved");
_Static_assert(__builtin_offsetof(struct fragment_caps, max_textures) == 12, "fragment_caps.max_textures moved");
struct wined3d_d3d_limits {
    unsigned int vs_version;
    unsigned int hs_version;
    unsigned int ds_version;
    unsigned int gs_version;
    unsigned int ps_version;
    unsigned int cs_version;
    unsigned int vs_uniform_count;
    unsigned int ps_uniform_count;
    unsigned int varying_count;
    unsigned int ffp_vertex_blend_matrices;
    unsigned int active_light_count;
    unsigned int max_rt_count;
    unsigned int max_clip_distances;
    unsigned int texture_size;
    unsigned int sample_count;
    float pointsize_max;
};
_Static_assert(sizeof(struct wined3d_d3d_limits) == 64, "wined3d_d3d_limits size");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_limits, vs_version) == 0, "wined3d_d3d_limits.vs_version moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_limits, hs_version) == 4, "wined3d_d3d_limits.hs_version moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_limits, ds_version) == 8, "wined3d_d3d_limits.ds_version moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_limits, gs_version) == 12, "wined3d_d3d_limits.gs_version moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_limits, ps_version) == 16, "wined3d_d3d_limits.ps_version moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_limits, cs_version) == 20, "wined3d_d3d_limits.cs_version moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_limits, vs_uniform_count) == 24, "wined3d_d3d_limits.vs_uniform_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_limits, ps_uniform_count) == 28, "wined3d_d3d_limits.ps_uniform_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_limits, varying_count) == 32, "wined3d_d3d_limits.varying_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_limits, ffp_vertex_blend_matrices) == 36, "wined3d_d3d_limits.ffp_vertex_blend_matrices moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_limits, active_light_count) == 40, "wined3d_d3d_limits.active_light_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_limits, max_rt_count) == 44, "wined3d_d3d_limits.max_rt_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_limits, max_clip_distances) == 48, "wined3d_d3d_limits.max_clip_distances moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_limits, texture_size) == 52, "wined3d_d3d_limits.texture_size moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_limits, sample_count) == 56, "wined3d_d3d_limits.sample_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_limits, pointsize_max) == 60, "wined3d_d3d_limits.pointsize_max moved");
struct wined3d_d3d_info {
    struct fragment_caps ffp_fragment_caps;
    struct wined3d_d3d_limits limits;
    unsigned int wined3d_creation_flags;
    unsigned int _bits84;
    unsigned int feature_level;
    unsigned int multisample_draw_location;
    float filling_convention_offset;
};
_Static_assert(sizeof(struct wined3d_d3d_info) == 100, "wined3d_d3d_info size");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_info, ffp_fragment_caps) == 0, "wined3d_d3d_info.ffp_fragment_caps moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_info, limits) == 16, "wined3d_d3d_info.limits moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_info, wined3d_creation_flags) == 80, "wined3d_d3d_info.wined3d_creation_flags moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_info, _bits84) == 84, "wined3d_d3d_info._bits84 moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_info, feature_level) == 88, "wined3d_d3d_info.feature_level moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_info, multisample_draw_location) == 92, "wined3d_d3d_info.multisample_draw_location moved");
_Static_assert(__builtin_offsetof(struct wined3d_d3d_info, filling_convention_offset) == 96, "wined3d_d3d_info.filling_convention_offset moved");
#define wined3d_d3d_info_get_emulated_flatshading(p)  ((((p)->_bits84) >> 0) & 0x1u)
#define wined3d_d3d_info_set_emulated_flatshading(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 0)) | (((v) & 0x1u) << 0)))
#define wined3d_d3d_info_get_ffp_alpha_test(p)  ((((p)->_bits84) >> 1) & 0x1u)
#define wined3d_d3d_info_set_ffp_alpha_test(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 1)) | (((v) & 0x1u) << 1)))
#define wined3d_d3d_info_get_shader_double_precision(p)  ((((p)->_bits84) >> 2) & 0x1u)
#define wined3d_d3d_info_set_shader_double_precision(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 2)) | (((v) & 0x1u) << 2)))
#define wined3d_d3d_info_get_shader_output_interpolation(p)  ((((p)->_bits84) >> 3) & 0x1u)
#define wined3d_d3d_info_set_shader_output_interpolation(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 3)) | (((v) & 0x1u) << 3)))
#define wined3d_d3d_info_get_viewport_array_index_any_shader(p)  ((((p)->_bits84) >> 4) & 0x1u)
#define wined3d_d3d_info_set_viewport_array_index_any_shader(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 4)) | (((v) & 0x1u) << 4)))
#define wined3d_d3d_info_get_simple_instancing(p)  ((((p)->_bits84) >> 5) & 0x1u)
#define wined3d_d3d_info_set_simple_instancing(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 5)) | (((v) & 0x1u) << 5)))
#define wined3d_d3d_info_get_min_max_filtering(p)  ((((p)->_bits84) >> 6) & 0x1u)
#define wined3d_d3d_info_set_min_max_filtering(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 6)) | (((v) & 0x1u) << 6)))
#define wined3d_d3d_info_get_stencil_export(p)  ((((p)->_bits84) >> 7) & 0x1u)
#define wined3d_d3d_info_set_stencil_export(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 7)) | (((v) & 0x1u) << 7)))
#define wined3d_d3d_info_get_unconditional_npot(p)  ((((p)->_bits84) >> 8) & 0x1u)
#define wined3d_d3d_info_set_unconditional_npot(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 8)) | (((v) & 0x1u) << 8)))
#define wined3d_d3d_info_get_draw_base_vertex_offset(p)  ((((p)->_bits84) >> 9) & 0x1u)
#define wined3d_d3d_info_set_draw_base_vertex_offset(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 9)) | (((v) & 0x1u) << 9)))
#define wined3d_d3d_info_get_vertex_bgra(p)  ((((p)->_bits84) >> 10) & 0x1u)
#define wined3d_d3d_info_set_vertex_bgra(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 10)) | (((v) & 0x1u) << 10)))
#define wined3d_d3d_info_get_texture_swizzle(p)  ((((p)->_bits84) >> 11) & 0x1u)
#define wined3d_d3d_info_set_texture_swizzle(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 11)) | (((v) & 0x1u) << 11)))
#define wined3d_d3d_info_get_srgb_read_control(p)  ((((p)->_bits84) >> 12) & 0x1u)
#define wined3d_d3d_info_set_srgb_read_control(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 12)) | (((v) & 0x1u) << 12)))
#define wined3d_d3d_info_get_srgb_write_control(p)  ((((p)->_bits84) >> 13) & 0x1u)
#define wined3d_d3d_info_set_srgb_write_control(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 13)) | (((v) & 0x1u) << 13)))
#define wined3d_d3d_info_get_clip_control(p)  ((((p)->_bits84) >> 14) & 0x1u)
#define wined3d_d3d_info_set_clip_control(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 14)) | (((v) & 0x1u) << 14)))
#define wined3d_d3d_info_get_full_ffp_varyings(p)  ((((p)->_bits84) >> 15) & 0x1u)
#define wined3d_d3d_info_set_full_ffp_varyings(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 15)) | (((v) & 0x1u) << 15)))
#define wined3d_d3d_info_get_scaled_resolve(p)  ((((p)->_bits84) >> 16) & 0x1u)
#define wined3d_d3d_info_set_scaled_resolve(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 16)) | (((v) & 0x1u) << 16)))
#define wined3d_d3d_info_get_pbo(p)  ((((p)->_bits84) >> 17) & 0x1u)
#define wined3d_d3d_info_set_pbo(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 17)) | (((v) & 0x1u) << 17)))
#define wined3d_d3d_info_get_subpixel_viewport(p)  ((((p)->_bits84) >> 18) & 0x1u)
#define wined3d_d3d_info_set_subpixel_viewport(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 18)) | (((v) & 0x1u) << 18)))
#define wined3d_d3d_info_get_is_gles(p)  ((((p)->_bits84) >> 19) & 0x1u)
#define wined3d_d3d_info_set_is_gles(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 19)) | (((v) & 0x1u) << 19)))
#define wined3d_d3d_info_get_fences(p)  ((((p)->_bits84) >> 20) & 0x1u)
#define wined3d_d3d_info_set_fences(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 20)) | (((v) & 0x1u) << 20)))
#define wined3d_d3d_info_get_persistent_map(p)  ((((p)->_bits84) >> 21) & 0x1u)
#define wined3d_d3d_info_set_persistent_map(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 21)) | (((v) & 0x1u) << 21)))
#define wined3d_d3d_info_get_gpu_push_constants(p)  ((((p)->_bits84) >> 22) & 0x1u)
#define wined3d_d3d_info_set_gpu_push_constants(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 22)) | (((v) & 0x1u) << 22)))
#define wined3d_d3d_info_get_ffp_hlsl(p)  ((((p)->_bits84) >> 23) & 0x1u)
#define wined3d_d3d_info_set_ffp_hlsl(p,v) ((p)->_bits84 = (((p)->_bits84 & ~(0x1u << 23)) | (((v) & 0x1u) << 23)))
struct wined3d_rational {
    unsigned int numerator;
    unsigned int denominator;
};
_Static_assert(sizeof(struct wined3d_rational) == 8, "wined3d_rational size");
_Static_assert(__builtin_offsetof(struct wined3d_rational, numerator) == 0, "wined3d_rational.numerator moved");
_Static_assert(__builtin_offsetof(struct wined3d_rational, denominator) == 4, "wined3d_rational.denominator moved");
struct wined3d_format {
    unsigned int id;
    unsigned int ddi_format;
    unsigned int component_count;
    unsigned int red_size;
    unsigned int green_size;
    unsigned int blue_size;
    unsigned int alpha_size;
    unsigned int red_offset;
    unsigned int green_offset;
    unsigned int blue_offset;
    unsigned int alpha_offset;
    unsigned int byte_count;
    unsigned char depth_size;
    unsigned char stencil_size;
    unsigned char _pad50[2];
    unsigned int block_width;
    unsigned int block_height;
    unsigned int block_byte_count;
    unsigned int plane_formats[2];
    unsigned int uv_width;
    unsigned int uv_height;
    unsigned int emit_idx;
    unsigned int conv_byte_count;
    unsigned int multisample_types;
    unsigned int attrs;
    unsigned int caps[6];
    float depth_bias_scale;
    struct wined3d_rational height_scale;
    struct color_fixup_desc color_fixup;
    unsigned char _pad134[2];
    void * upload;
    void * download;
    void * decompress;
    unsigned int typeless_id;
};
_Static_assert(sizeof(struct wined3d_format) == 152, "wined3d_format size");
_Static_assert(__builtin_offsetof(struct wined3d_format, id) == 0, "wined3d_format.id moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, ddi_format) == 4, "wined3d_format.ddi_format moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, component_count) == 8, "wined3d_format.component_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, red_size) == 12, "wined3d_format.red_size moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, green_size) == 16, "wined3d_format.green_size moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, blue_size) == 20, "wined3d_format.blue_size moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, alpha_size) == 24, "wined3d_format.alpha_size moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, red_offset) == 28, "wined3d_format.red_offset moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, green_offset) == 32, "wined3d_format.green_offset moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, blue_offset) == 36, "wined3d_format.blue_offset moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, alpha_offset) == 40, "wined3d_format.alpha_offset moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, byte_count) == 44, "wined3d_format.byte_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, depth_size) == 48, "wined3d_format.depth_size moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, stencil_size) == 49, "wined3d_format.stencil_size moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, block_width) == 52, "wined3d_format.block_width moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, block_height) == 56, "wined3d_format.block_height moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, block_byte_count) == 60, "wined3d_format.block_byte_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, plane_formats) == 64, "wined3d_format.plane_formats moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, uv_width) == 72, "wined3d_format.uv_width moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, uv_height) == 76, "wined3d_format.uv_height moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, emit_idx) == 80, "wined3d_format.emit_idx moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, conv_byte_count) == 84, "wined3d_format.conv_byte_count moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, multisample_types) == 88, "wined3d_format.multisample_types moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, attrs) == 92, "wined3d_format.attrs moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, caps) == 96, "wined3d_format.caps moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, depth_bias_scale) == 120, "wined3d_format.depth_bias_scale moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, height_scale) == 124, "wined3d_format.height_scale moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, color_fixup) == 132, "wined3d_format.color_fixup moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, upload) == 136, "wined3d_format.upload moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, download) == 140, "wined3d_format.download moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, decompress) == 144, "wined3d_format.decompress moved");
_Static_assert(__builtin_offsetof(struct wined3d_format, typeless_id) == 148, "wined3d_format.typeless_id moved");
