/* generated from the shipped i386 build's DWARF -- do not edit */
/* Self-check: a reconstruction that does not reproduce the shipped
   sizeof is lossy, and any comparison built on it is void. The static
   assertions below fail the build rather than produce a false result. */
#define offsetof(t,m) __builtin_offsetof(t,m)
struct g_wined3d_fb_state {
    void * render_targets[8];
    void * depth_stencil;
};
struct g_wined3d_stream_output {
    void * buffer;
    unsigned int offset;
};
struct g_wined3d_stream_state {
    void * buffer;
    unsigned int offset;
    unsigned int stride;
    unsigned int frequency;
    unsigned int flags;
};
struct g_wined3d_constant_buffer_state {
    void * buffer;
    unsigned int offset;
    unsigned int size;
};
struct g_wined3d_viewport {
    float x;
    float y;
    float width;
    float height;
    float min_z;
    float max_z;
};
struct g_tagRECT {
    int left;
    int top;
    int right;
    int bottom;
};
struct g_rb_tree {
    void * compare;
    void * root;
};
struct g_wined3d_light_state {
    struct g_rb_tree lights_tree;
    void * lights[8];
};
struct g_wined3d_color {
    float r;
    float g;
    float b;
    float a;
};
struct g_wined3d_extra_vs_args {
    unsigned char clip_planes;
    unsigned char pixel_fog;
    unsigned char flat_shading;
    unsigned char ortho_fog;
};
struct g_wined3d_extra_ps_args {
    unsigned char point_sprite;
    unsigned char flat_shading;
    unsigned char fog_enable;
    unsigned char srgb_write;
    int fog_mode;
    int alpha_func;
    unsigned int texcoord_index[8];
    unsigned int texture_transform_flags[4];
};
struct g_wined3d_state {
    int feature_level;
    unsigned int flags;
    struct g_wined3d_fb_state fb;
    void * vertex_declaration;
    struct g_wined3d_stream_output stream_output[4];
    struct g_wined3d_stream_state streams[16];
    void * index_buffer;
    int index_format;
    unsigned int index_offset;
    int base_vertex_index;
    int load_base_vertex_index;
    int primitive_type;
    unsigned int patch_vertex_count;
    void * predicate;
    int predicate_value;
    void * shader[6];
    struct g_wined3d_constant_buffer_state cb[6][15];
    void * sampler[6][16];
    void * shader_resource_view[6][128];
    void * unordered_access_view[2][8];
    unsigned int texture_states[8][18];
    struct g_wined3d_viewport viewports[16];
    unsigned int viewport_count;
    struct g_tagRECT scissor_rects[16];
    unsigned int scissor_rect_count;
    struct g_wined3d_light_state light_state;
    unsigned int render_states[210];
    void * blend_state;
    struct g_wined3d_color blend_factor;
    unsigned int sample_mask;
    void * depth_stencil_state;
    unsigned int stencil_ref;
    struct g_wined3d_extra_vs_args extra_vs_args;
    struct g_wined3d_extra_ps_args extra_ps_args;
    unsigned char depth_bounds_enable;
    float depth_bounds_min;
    float depth_bounds_max;
    void * rasterizer_state;
};
struct g_anon_1 {
    void * texture;
    unsigned int sub_resource_idx;
};
struct g_wined3d_bo_address {
    void * buffer_object;
    void * addr;
};
struct g_wined3d_stream_info_element {
    void * format;
    struct g_wined3d_bo_address data;
    unsigned int stride;
    unsigned int stream_idx;
    unsigned int divisor;
    unsigned char instanced;
};
struct g_wined3d_stream_info {
    struct g_wined3d_stream_info_element elements[32];
    unsigned int position_transformed : 1;
    unsigned int all_vbo : 1;
    unsigned int swizzle_map;
    unsigned int use_map;
};
struct g_wined3d_context {
    void * d3d_info;
    void * state_table;
    unsigned int dirty_graphics_states[12];
    unsigned int dirty_compute_states[1];
    void * device;
    void * swapchain;
    struct g_anon_1 current_rt;
    unsigned int last_swizzle_map;
    unsigned int shader_update_mask : 6;
    unsigned int update_shader_resource_bindings : 1;
    unsigned int update_compute_shader_resource_bindings : 1;
    unsigned int last_was_rhw : 1;
    unsigned int last_was_ffp_blit : 1;
    unsigned int last_was_blit : 1;
    unsigned int last_was_dual_source_blend : 1;
    unsigned int lowest_disabled_stage : 4;
    unsigned int fixed_function_usage_map : 8;
    unsigned int uses_uavs : 1;
    unsigned int uses_fbo_attached_resources : 1;
    unsigned int transform_feedback_active : 1;
    unsigned int transform_feedback_paused : 1;
    unsigned int current : 1;
    unsigned int destroyed : 1;
    unsigned int destroy_delayed : 1;
    unsigned int update_unordered_access_view_bindings : 1;
    unsigned int update_compute_unordered_access_view_bindings : 1;
    unsigned int update_primitive_type : 1;
    unsigned int update_multisample_state : 1;
    unsigned int update_patch_vertex_count : 1;
    unsigned int padding : 28;
    unsigned int clip_distance_mask : 8;
    unsigned int constant_update_mask;
    unsigned int numbered_array_mask;
    void * shader_backend_data;
    struct g_wined3d_stream_info stream_info;
    unsigned int viewport_count;
    unsigned int scissor_rect_count;
};
struct g_wined3d_state_entry {
    unsigned int representative;
    void * apply;
};
struct g_wined3d_device_creation_parameters {
    unsigned int adapter_idx;
    int device_type;
    void * focus_window;
    unsigned int flags;
};
struct g_list {
    void * next;
    void * prev;
};
struct g__RTL_CRITICAL_SECTION {
    void * DebugInfo;
    int LockCount;
    int RecursionCount;
    void * OwningThread;
    void * LockSemaphore;
    unsigned int SpinCount;
};
struct g_wined3d_device {
    int ref;
    void * device_parent;
    void * wined3d;
    void * adapter;
    void * shader_backend;
    void * shader_priv;
    void * fragment_priv;
    void * vertex_priv;
    struct g_wined3d_state_entry state_table[385];
    void * multistate_funcs[385];
    void * blitter;
    unsigned char bCursorVisible : 1;
    unsigned char d3d_initialized : 1;
    unsigned char inScene : 1;
    unsigned char softwareVertexProcessing : 1;
    unsigned char restore_screensaver : 1;
    unsigned char padding : 3;
    unsigned char surface_alignment;
    unsigned short padding2 : 16;
    struct g_wined3d_device_creation_parameters create_parms;
    void * focus_window;
    void * back_buffer_view;
    void * swapchains;
    unsigned int swapchain_count;
    unsigned int max_frame_latency;
    struct g_list resources;
    struct g_list shaders;
    struct g_rb_tree so_descs;
    struct g_rb_tree samplers;
    struct g_rb_tree rasterizer_states;
    struct g_rb_tree blend_states;
    struct g_rb_tree depth_stencil_states;
    struct g_rb_tree ffp_vertex_shaders;
    struct g_rb_tree ffp_pixel_shaders;
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
    struct g__RTL_CRITICAL_SECTION bo_map_lock;
};
struct g_wined3d_const_bo_address {
    void * buffer_object;
    void * addr;
};
struct g_upload_bo {
    struct g_wined3d_const_bo_address addr;
    unsigned int flags;
};
struct g_wined3d_box {
    unsigned int left;
    unsigned int top;
    unsigned int right;
    unsigned int bottom;
    unsigned int front;
    unsigned int back;
};
struct g_wined3d_client_resource {
    struct g_wined3d_bo_address addr;
    struct g_upload_bo mapped_upload;
    struct g_wined3d_box mapped_box;
};
struct g_wined3d_resource {
    int ref;
    int bind_count;
    int map_count;
    unsigned int access_time;
    void * device;
    int type;
    int gl_type;
    void * format;
    unsigned int format_attrs;
    unsigned int format_caps;
    int multisample_type;
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
    unsigned int pin_sysmem : 1;
    struct g_wined3d_client_resource client;
    void * parent;
    void * parent_ops;
    void * resource_ops;
    struct g_list resource_list_entry;
    int srv_bind_count_device;
    int rtv_bind_count_device;
};
struct g_wined3d_bo_user {
    struct g_list entry;
    unsigned char valid;
};
struct g_wined3d_buffer {
    struct g_wined3d_resource resource;
    void * buffer_ops;
    unsigned int structure_byte_stride;
    unsigned int flags;
    unsigned int locations;
    void * map_ptr;
    void * buffer_object;
    struct g_wined3d_bo_user bo_user;
    void * dirty_ranges;
    unsigned int dirty_range_count;
    unsigned int dirty_ranges_capacity;
};
struct g_wined3d_color_key {
    unsigned int color_space_low_value;
    unsigned int color_space_high_value;
};
struct g_wined3d_texture_async {
    unsigned int flags;
    struct g_wined3d_color_key dst_blt_color_key;
    struct g_wined3d_color_key src_blt_color_key;
    struct g_wined3d_color_key dst_overlay_color_key;
    struct g_wined3d_color_key src_overlay_color_key;
    struct g_wined3d_color_key gl_color_key;
    unsigned int color_key_flags;
};
struct g_wined3d_texture {
    struct g_wined3d_resource resource;
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
    struct g_wined3d_texture_async async;
    struct g_wined3d_color_key src_blt_color_key;
    unsigned int color_key_flags;
    void * dirty_regions;
    void * overlay_info;
    void * dc_info;
    void * sub_resources;
};
_Static_assert(sizeof(struct g_wined3d_state) == 7276, "lossy reconstruction of wined3d_state");
_Static_assert(sizeof(struct g_wined3d_context) == 1020, "lossy reconstruction of wined3d_context");
_Static_assert(sizeof(struct g_wined3d_device) == 4884, "lossy reconstruction of wined3d_device");
_Static_assert(sizeof(struct g_wined3d_buffer) == 216, "lossy reconstruction of wined3d_buffer");
_Static_assert(sizeof(struct g_wined3d_texture) == 292, "lossy reconstruction of wined3d_texture");
_Static_assert(sizeof(struct g_wined3d_resource) == 168, "lossy reconstruction of wined3d_resource");
_Static_assert(sizeof(struct g_wined3d_stream_info) == 908, "lossy reconstruction of wined3d_stream_info");

const unsigned int probe_table[] = {
    sizeof(struct g_wined3d_state), _Alignof(struct g_wined3d_state),
    offsetof(struct g_wined3d_state, feature_level),
    offsetof(struct g_wined3d_state, flags),
    offsetof(struct g_wined3d_state, fb),
    offsetof(struct g_wined3d_state, vertex_declaration),
    offsetof(struct g_wined3d_state, stream_output),
    offsetof(struct g_wined3d_state, streams),
    offsetof(struct g_wined3d_state, index_buffer),
    offsetof(struct g_wined3d_state, index_format),
    offsetof(struct g_wined3d_state, index_offset),
    offsetof(struct g_wined3d_state, base_vertex_index),
    offsetof(struct g_wined3d_state, load_base_vertex_index),
    offsetof(struct g_wined3d_state, primitive_type),
    offsetof(struct g_wined3d_state, patch_vertex_count),
    offsetof(struct g_wined3d_state, predicate),
    offsetof(struct g_wined3d_state, predicate_value),
    offsetof(struct g_wined3d_state, shader),
    offsetof(struct g_wined3d_state, cb),
    offsetof(struct g_wined3d_state, sampler),
    offsetof(struct g_wined3d_state, shader_resource_view),
    offsetof(struct g_wined3d_state, unordered_access_view),
    offsetof(struct g_wined3d_state, texture_states),
    offsetof(struct g_wined3d_state, viewports),
    offsetof(struct g_wined3d_state, viewport_count),
    offsetof(struct g_wined3d_state, scissor_rects),
    offsetof(struct g_wined3d_state, scissor_rect_count),
    offsetof(struct g_wined3d_state, light_state),
    offsetof(struct g_wined3d_state, render_states),
    offsetof(struct g_wined3d_state, blend_state),
    offsetof(struct g_wined3d_state, blend_factor),
    offsetof(struct g_wined3d_state, sample_mask),
    offsetof(struct g_wined3d_state, depth_stencil_state),
    offsetof(struct g_wined3d_state, stencil_ref),
    offsetof(struct g_wined3d_state, extra_vs_args),
    offsetof(struct g_wined3d_state, extra_ps_args),
    offsetof(struct g_wined3d_state, depth_bounds_enable),
    offsetof(struct g_wined3d_state, depth_bounds_min),
    offsetof(struct g_wined3d_state, depth_bounds_max),
    offsetof(struct g_wined3d_state, rasterizer_state),
    sizeof(struct g_wined3d_context), _Alignof(struct g_wined3d_context),
    offsetof(struct g_wined3d_context, d3d_info),
    offsetof(struct g_wined3d_context, state_table),
    offsetof(struct g_wined3d_context, dirty_graphics_states),
    offsetof(struct g_wined3d_context, dirty_compute_states),
    offsetof(struct g_wined3d_context, device),
    offsetof(struct g_wined3d_context, swapchain),
    offsetof(struct g_wined3d_context, current_rt),
    offsetof(struct g_wined3d_context, last_swizzle_map),
    offsetof(struct g_wined3d_context, constant_update_mask),
    offsetof(struct g_wined3d_context, numbered_array_mask),
    offsetof(struct g_wined3d_context, shader_backend_data),
    offsetof(struct g_wined3d_context, stream_info),
    offsetof(struct g_wined3d_context, viewport_count),
    offsetof(struct g_wined3d_context, scissor_rect_count),
    sizeof(struct g_wined3d_device), _Alignof(struct g_wined3d_device),
    offsetof(struct g_wined3d_device, ref),
    offsetof(struct g_wined3d_device, device_parent),
    offsetof(struct g_wined3d_device, wined3d),
    offsetof(struct g_wined3d_device, adapter),
    offsetof(struct g_wined3d_device, shader_backend),
    offsetof(struct g_wined3d_device, shader_priv),
    offsetof(struct g_wined3d_device, fragment_priv),
    offsetof(struct g_wined3d_device, vertex_priv),
    offsetof(struct g_wined3d_device, state_table),
    offsetof(struct g_wined3d_device, multistate_funcs),
    offsetof(struct g_wined3d_device, blitter),
    offsetof(struct g_wined3d_device, surface_alignment),
    offsetof(struct g_wined3d_device, create_parms),
    offsetof(struct g_wined3d_device, focus_window),
    offsetof(struct g_wined3d_device, back_buffer_view),
    offsetof(struct g_wined3d_device, swapchains),
    offsetof(struct g_wined3d_device, swapchain_count),
    offsetof(struct g_wined3d_device, max_frame_latency),
    offsetof(struct g_wined3d_device, resources),
    offsetof(struct g_wined3d_device, shaders),
    offsetof(struct g_wined3d_device, so_descs),
    offsetof(struct g_wined3d_device, samplers),
    offsetof(struct g_wined3d_device, rasterizer_states),
    offsetof(struct g_wined3d_device, blend_states),
    offsetof(struct g_wined3d_device, depth_stencil_states),
    offsetof(struct g_wined3d_device, ffp_vertex_shaders),
    offsetof(struct g_wined3d_device, ffp_pixel_shaders),
    offsetof(struct g_wined3d_device, auto_depth_stencil_view),
    offsetof(struct g_wined3d_device, xHotSpot),
    offsetof(struct g_wined3d_device, yHotSpot),
    offsetof(struct g_wined3d_device, xScreenSpace),
    offsetof(struct g_wined3d_device, yScreenSpace),
    offsetof(struct g_wined3d_device, cursorWidth),
    offsetof(struct g_wined3d_device, cursorHeight),
    offsetof(struct g_wined3d_device, cursor_texture),
    offsetof(struct g_wined3d_device, hardwareCursor),
    offsetof(struct g_wined3d_device, logo_texture),
    offsetof(struct g_wined3d_device, default_sampler),
    offsetof(struct g_wined3d_device, null_sampler),
    offsetof(struct g_wined3d_device, cs),
    offsetof(struct g_wined3d_device, push_constants),
    offsetof(struct g_wined3d_device, contexts),
    offsetof(struct g_wined3d_device, context_count),
    offsetof(struct g_wined3d_device, bo_map_lock),
    sizeof(struct g_wined3d_buffer), _Alignof(struct g_wined3d_buffer),
    offsetof(struct g_wined3d_buffer, resource),
    offsetof(struct g_wined3d_buffer, buffer_ops),
    offsetof(struct g_wined3d_buffer, structure_byte_stride),
    offsetof(struct g_wined3d_buffer, flags),
    offsetof(struct g_wined3d_buffer, locations),
    offsetof(struct g_wined3d_buffer, map_ptr),
    offsetof(struct g_wined3d_buffer, buffer_object),
    offsetof(struct g_wined3d_buffer, bo_user),
    offsetof(struct g_wined3d_buffer, dirty_ranges),
    offsetof(struct g_wined3d_buffer, dirty_range_count),
    offsetof(struct g_wined3d_buffer, dirty_ranges_capacity),
    sizeof(struct g_wined3d_texture), _Alignof(struct g_wined3d_texture),
    offsetof(struct g_wined3d_texture, resource),
    offsetof(struct g_wined3d_texture, texture_ops),
    offsetof(struct g_wined3d_texture, swapchain),
    offsetof(struct g_wined3d_texture, layer_count),
    offsetof(struct g_wined3d_texture, level_count),
    offsetof(struct g_wined3d_texture, download_count),
    offsetof(struct g_wined3d_texture, sysmem_count),
    offsetof(struct g_wined3d_texture, lod),
    offsetof(struct g_wined3d_texture, flags),
    offsetof(struct g_wined3d_texture, update_map_binding),
    offsetof(struct g_wined3d_texture, row_pitch),
    offsetof(struct g_wined3d_texture, slice_pitch),
    offsetof(struct g_wined3d_texture, identity_srv),
    offsetof(struct g_wined3d_texture, async),
    offsetof(struct g_wined3d_texture, src_blt_color_key),
    offsetof(struct g_wined3d_texture, color_key_flags),
    offsetof(struct g_wined3d_texture, dirty_regions),
    offsetof(struct g_wined3d_texture, overlay_info),
    offsetof(struct g_wined3d_texture, dc_info),
    offsetof(struct g_wined3d_texture, sub_resources),
    sizeof(struct g_wined3d_resource), _Alignof(struct g_wined3d_resource),
    offsetof(struct g_wined3d_resource, ref),
    offsetof(struct g_wined3d_resource, bind_count),
    offsetof(struct g_wined3d_resource, map_count),
    offsetof(struct g_wined3d_resource, access_time),
    offsetof(struct g_wined3d_resource, device),
    offsetof(struct g_wined3d_resource, type),
    offsetof(struct g_wined3d_resource, gl_type),
    offsetof(struct g_wined3d_resource, format),
    offsetof(struct g_wined3d_resource, format_attrs),
    offsetof(struct g_wined3d_resource, format_caps),
    offsetof(struct g_wined3d_resource, multisample_type),
    offsetof(struct g_wined3d_resource, multisample_quality),
    offsetof(struct g_wined3d_resource, usage),
    offsetof(struct g_wined3d_resource, bind_flags),
    offsetof(struct g_wined3d_resource, access),
    offsetof(struct g_wined3d_resource, draw_binding),
    offsetof(struct g_wined3d_resource, map_binding),
    offsetof(struct g_wined3d_resource, width),
    offsetof(struct g_wined3d_resource, height),
    offsetof(struct g_wined3d_resource, depth),
    offsetof(struct g_wined3d_resource, size),
    offsetof(struct g_wined3d_resource, priority),
    offsetof(struct g_wined3d_resource, heap_pointer),
    offsetof(struct g_wined3d_resource, heap_memory),
    offsetof(struct g_wined3d_resource, client),
    offsetof(struct g_wined3d_resource, parent),
    offsetof(struct g_wined3d_resource, parent_ops),
    offsetof(struct g_wined3d_resource, resource_ops),
    offsetof(struct g_wined3d_resource, resource_list_entry),
    offsetof(struct g_wined3d_resource, srv_bind_count_device),
    offsetof(struct g_wined3d_resource, rtv_bind_count_device),
    sizeof(struct g_wined3d_stream_info), _Alignof(struct g_wined3d_stream_info),
    offsetof(struct g_wined3d_stream_info, elements),
    offsetof(struct g_wined3d_stream_info, swizzle_map),
    offsetof(struct g_wined3d_stream_info, use_map),
};
