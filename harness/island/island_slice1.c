/* mgs2 island, slice 1: wined3d_ffp_get_fs_settings compiled for ARM.
 * Function and helpers verbatim from the shipping WineD3D source. */
typedef int BOOL;
typedef unsigned int UINT, DWORD, uint32_t;
typedef long LONG;
#define TRUE 1
#define FALSE 0
#define NULL ((void *)0)
#define assert(x) ((void)0)
#define WINED3D_MAX_FFP_TEXTURES 8
void *memset(void *, int, unsigned int);

struct list;
struct rb_entry;
struct wined3d_blend_state;
struct wined3d_bo;
struct wined3d_buffer;
struct wined3d_dc_info;
struct wined3d_depth_stencil_state;
struct wined3d_device;
struct wined3d_dirty_regions;
struct wined3d_format;
struct wined3d_light_info;
struct wined3d_overlay_info;
struct wined3d_parent_ops;
struct wined3d_query;
struct wined3d_rasterizer_state;
struct wined3d_rendertarget_view;
struct wined3d_resource;
struct wined3d_resource_ops;
struct wined3d_sampler;
struct wined3d_shader;
struct wined3d_shader_frontend;
struct wined3d_shader_immediate_constant_buffer;
struct wined3d_shader_limits;
struct wined3d_shader_phase;
struct wined3d_shader_resource_view;
struct wined3d_shader_sampler_map_entry;
struct wined3d_shader_signature_element;
struct wined3d_shader_tgsm;
struct wined3d_stream_output_desc;
struct wined3d_swapchain;
struct wined3d_texture_ops;
struct wined3d_texture_sub_resource;
struct wined3d_unordered_access_view;
struct wined3d_vertex_declaration;
struct wined3d_vertex_declaration_element;
struct wined3d_fb_state {
    struct wined3d_rendertarget_view * render_targets[8];
    struct wined3d_rendertarget_view * depth_stencil;
};
struct wined3d_stream_output {
    struct wined3d_buffer * buffer;
    unsigned int offset;
};
struct wined3d_stream_state {
    struct wined3d_buffer * buffer;
    unsigned int offset;
    unsigned int stride;
    unsigned int frequency;
    unsigned int flags;
};
struct wined3d_constant_buffer_state {
    struct wined3d_buffer * buffer;
    unsigned int offset;
    unsigned int size;
};
struct wined3d_viewport {
    float x;
    float y;
    float width;
    float height;
    float min_z;
    float max_z;
};
struct tagRECT {
    int left;
    int top;
    int right;
    int bottom;
};
struct rb_tree {
    void * compare;
    struct rb_entry * root;
};
struct wined3d_light_state {
    struct rb_tree lights_tree;
    struct wined3d_light_info * lights[8];
};
struct wined3d_color {
    float r;
    float g;
    float b;
    float a;
};
struct wined3d_extra_vs_args {
    unsigned char clip_planes;
    unsigned char pixel_fog;
    unsigned char flat_shading;
    unsigned char ortho_fog;
};
struct wined3d_extra_ps_args {
    unsigned char point_sprite;
    unsigned char flat_shading;
    unsigned char fog_enable;
    unsigned char srgb_write;
    int fog_mode;
    int alpha_func;
    unsigned int texcoord_index[8];
    unsigned int texture_transform_flags[4];
};
struct wined3d_state {
    int feature_level;
    unsigned int flags;
    struct wined3d_fb_state fb;
    struct wined3d_vertex_declaration * vertex_declaration;
    struct wined3d_stream_output stream_output[4];
    struct wined3d_stream_state streams[16];
    struct wined3d_buffer * index_buffer;
    int index_format;
    unsigned int index_offset;
    int base_vertex_index;
    int load_base_vertex_index;
    int primitive_type;
    unsigned int patch_vertex_count;
    struct wined3d_query * predicate;
    int predicate_value;
    struct wined3d_shader * shader[6];
    struct wined3d_constant_buffer_state cb[6][15];
    struct wined3d_sampler * sampler[6][16];
    struct wined3d_shader_resource_view * shader_resource_view[6][128];
    struct wined3d_unordered_access_view * unordered_access_view[2][8];
    unsigned int texture_states[8][18];
    struct wined3d_viewport viewports[16];
    unsigned int viewport_count;
    struct tagRECT scissor_rects[16];
    unsigned int scissor_rect_count;
    struct wined3d_light_state light_state;
    unsigned int render_states[210];
    struct wined3d_blend_state * blend_state;
    struct wined3d_color blend_factor;
    unsigned int sample_mask;
    struct wined3d_depth_stencil_state * depth_stencil_state;
    unsigned int stencil_ref;
    struct wined3d_extra_vs_args extra_vs_args;
    struct wined3d_extra_ps_args extra_ps_args;
    unsigned char depth_bounds_enable;
    float depth_bounds_min;
    float depth_bounds_max;
    struct wined3d_rasterizer_state * rasterizer_state;
};
struct fragment_caps {
    unsigned int PrimitiveMiscCaps;
    unsigned int TextureOpCaps;
    unsigned int max_blend_stages;
    unsigned int max_textures;
};
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
struct wined3d_d3d_info {
    struct fragment_caps ffp_fragment_caps;
    struct wined3d_d3d_limits limits;
    unsigned int wined3d_creation_flags;
    unsigned int emulated_flatshading : 1;
    unsigned int ffp_alpha_test : 1;
    unsigned int shader_double_precision : 1;
    unsigned int shader_output_interpolation : 1;
    unsigned int viewport_array_index_any_shader : 1;
    unsigned int simple_instancing : 1;
    unsigned int min_max_filtering : 1;
    unsigned int stencil_export : 1;
    unsigned int unconditional_npot : 1;
    unsigned int draw_base_vertex_offset : 1;
    unsigned int vertex_bgra : 1;
    unsigned int texture_swizzle : 1;
    unsigned int srgb_read_control : 1;
    unsigned int srgb_write_control : 1;
    unsigned int clip_control : 1;
    unsigned int full_ffp_varyings : 1;
    unsigned int scaled_resolve : 1;
    unsigned int pbo : 1;
    unsigned int subpixel_viewport : 1;
    unsigned int is_gles : 1;
    unsigned int fences : 1;
    unsigned int persistent_map : 1;
    unsigned int gpu_push_constants : 1;
    unsigned int ffp_hlsl : 1;
    int feature_level;
    unsigned int multisample_draw_location;
    float filling_convention_offset;
};
struct color_fixup_desc {
    unsigned short x_sign_fixup : 1;
    unsigned short x_source : 3;
    unsigned short y_sign_fixup : 1;
    unsigned short y_source : 3;
    unsigned short z_sign_fixup : 1;
    unsigned short z_source : 3;
    unsigned short w_sign_fixup : 1;
    unsigned short w_source : 3;
};
struct texture_stage_op {
    unsigned int cop : 8;
    unsigned int carg1 : 8;
    unsigned int carg2 : 8;
    unsigned int carg0 : 8;
    unsigned int aop : 8;
    unsigned int aarg1 : 8;
    unsigned int aarg2 : 8;
    unsigned int aarg0 : 8;
    struct color_fixup_desc color_fixup;
    unsigned short _mgs2_ms_bitfield_pad;
    unsigned int tex_type : 3;
    unsigned int tmp_dst : 1;
    unsigned int projected : 1;
    unsigned int padding : 11;
};
struct ffp_frag_settings {
    struct texture_stage_op op[8];
    unsigned char fog;
    unsigned char sRGB_write;
    unsigned char texcoords_initialized;
    unsigned char color_key_enabled : 1;
    unsigned char pointsprite : 1;
    unsigned char flatshading : 1;
    unsigned char alpha_test_func : 3;
    unsigned char padding : 2;
};
struct wined3d_bo_address {
    struct wined3d_bo * buffer_object;
    void * addr;
};
struct wined3d_const_bo_address {
    struct wined3d_bo * buffer_object;
    void * addr;
};
struct upload_bo {
    struct wined3d_const_bo_address addr;
    unsigned int flags;
};
struct wined3d_box {
    unsigned int left;
    unsigned int top;
    unsigned int right;
    unsigned int bottom;
    unsigned int front;
    unsigned int back;
};
struct wined3d_client_resource {
    struct wined3d_bo_address addr;
    struct upload_bo mapped_upload;
    struct wined3d_box mapped_box;
};
struct list {
    struct list * next;
    struct list * prev;
};
struct wined3d_resource {
    int ref;
    int bind_count;
    int map_count;
    unsigned int access_time;
    struct wined3d_device * device;
    int type;
    int gl_type;
    struct wined3d_format * format;
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
    struct wined3d_client_resource client;
    void * parent;
    struct wined3d_parent_ops * parent_ops;
    struct wined3d_resource_ops * resource_ops;
    struct list resource_list_entry;
    int srv_bind_count_device;
    int rtv_bind_count_device;
};
struct wined3d_color_key {
    unsigned int color_space_low_value;
    unsigned int color_space_high_value;
};
struct wined3d_texture_async {
    unsigned int flags;
    struct wined3d_color_key dst_blt_color_key;
    struct wined3d_color_key src_blt_color_key;
    struct wined3d_color_key dst_overlay_color_key;
    struct wined3d_color_key src_overlay_color_key;
    struct wined3d_color_key gl_color_key;
    unsigned int color_key_flags;
};
struct wined3d_texture {
    struct wined3d_resource resource;
    struct wined3d_texture_ops * texture_ops;
    struct wined3d_swapchain * swapchain;
    unsigned int layer_count;
    unsigned int level_count;
    unsigned int download_count;
    unsigned int sysmem_count;
    unsigned int lod;
    unsigned int flags;
    unsigned int update_map_binding;
    unsigned int row_pitch;
    unsigned int slice_pitch;
    struct wined3d_shader_resource_view * identity_srv;
    struct wined3d_texture_async async;
    struct wined3d_color_key src_blt_color_key;
    unsigned int color_key_flags;
    struct wined3d_dirty_regions * dirty_regions;
    struct wined3d_overlay_info * overlay_info;
    struct wined3d_dc_info * dc_info;
    struct wined3d_texture_sub_resource * sub_resources;
};
struct anon_2 {
    unsigned int start_idx;
    unsigned int count;
};
struct anon_3 {
    unsigned int level_idx;
    unsigned int level_count;
    unsigned int layer_idx;
    unsigned int layer_count;
};
union anon_1 {
    struct anon_2 buffer;
    struct anon_3 texture;
};
struct wined3d_view_desc {
    int format_id;
    unsigned int flags;
    union anon_1 u;
};
struct wined3d_shader_resource_view {
    int refcount;
    struct wined3d_resource * resource;
    void * parent;
    struct wined3d_parent_ops * parent_ops;
    struct wined3d_format * format;
    struct wined3d_view_desc desc;
};
struct wined3d_stream_info_element {
    struct wined3d_format * format;
    struct wined3d_bo_address data;
    unsigned int stride;
    unsigned int stream_idx;
    unsigned int divisor;
    unsigned char instanced;
};
struct wined3d_stream_info {
    struct wined3d_stream_info_element elements[32];
    unsigned int position_transformed : 1;
    unsigned int all_vbo : 1;
    unsigned int swizzle_map;
    unsigned int use_map;
};
struct wined3d_rational {
    unsigned int numerator;
    unsigned int denominator;
};
struct wined3d_format {
    int id;
    int ddi_format;
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
    unsigned int block_width;
    unsigned int block_height;
    unsigned int block_byte_count;
    int plane_formats[2];
    unsigned int uv_width;
    unsigned int uv_height;
    int emit_idx;
    unsigned int conv_byte_count;
    unsigned int multisample_types;
    unsigned int attrs;
    unsigned int caps[6];
    float depth_bias_scale;
    struct wined3d_rational height_scale;
    struct color_fixup_desc color_fixup;
    void * upload;
    void * download;
    void * decompress;
    int typeless_id;
};
struct wined3d_shader_version {
    int type;
    unsigned char major;
    unsigned char minor;
};
union anon_4 {
    unsigned int texcoord_mask[8];
    unsigned char output_registers_mask[32];
};
struct wined3d_shader_resource_info {
    int type;
    int data_type;
    unsigned int flags;
    unsigned int stride;
};
struct wined3d_shader_sampler_map {
    struct wined3d_shader_sampler_map_entry * entries;
    unsigned int size;
    unsigned int count;
};
struct wined3d_shader_reg_maps {
    struct wined3d_shader_version shader_version;
    unsigned char texcoord;
    unsigned char address;
    unsigned short labels;
    unsigned int temporary;
    unsigned int temporary_count;
    void * constf;
    struct list indexable_temps;
    struct wined3d_shader_immediate_constant_buffer * icb;
    union anon_4 u;
    unsigned int input_registers;
    unsigned int output_registers;
    unsigned short integer_constants;
    unsigned short boolean_constants;
    unsigned short local_int_consts;
    unsigned short local_bool_consts;
    unsigned int cb_sizes[15];
    unsigned int cb_map;
    struct wined3d_shader_resource_info resource_info[128];
    unsigned int resource_map[4];
    struct wined3d_shader_sampler_map sampler_map;
    unsigned int sampler_comparison_mode;
    unsigned char bumpmat;
    unsigned char luminanceparams;
    struct wined3d_shader_resource_info uav_resource_info[8];
    unsigned int uav_read_mask : 8;
    unsigned int uav_counter_mask : 8;
    unsigned int clip_distance_mask : 8;
    unsigned int cull_distance_mask : 8;
    unsigned int usesnrm : 1;
    unsigned int vpos : 1;
    unsigned int usesdsx : 1;
    unsigned int usesdsy : 1;
    unsigned int usestexldd : 1;
    unsigned int usesmova : 1;
    unsigned int usesfacing : 1;
    unsigned int usesrelconstF : 1;
    unsigned int fog : 1;
    unsigned int usestexldl : 1;
    unsigned int usesifc : 1;
    unsigned int usescall : 1;
    unsigned int usespow : 1;
    unsigned int point_size : 1;
    unsigned int vocp : 1;
    unsigned int input_rel_addressing : 1;
    unsigned int viewport_array : 1;
    unsigned int sample_mask : 1;
    unsigned int stencil_ref : 1;
    unsigned int rt_mask;
    unsigned int loop_depth;
    unsigned int min_rel_offset;
    unsigned int max_rel_offset;
    struct wined3d_shader_tgsm * tgsm;
    unsigned int tgsm_capacity;
    unsigned int tgsm_count;
};
struct wined3d_shader_signature {
    unsigned int element_count;
    struct wined3d_shader_signature_element * elements;
};
struct wined3d_shader_attribute {
    int usage;
    unsigned int usage_idx;
};
struct wined3d_vertex_shader {
    struct wined3d_shader_attribute attributes[32];
};
struct anon_6 {
    struct wined3d_shader_phase * control_point;
    unsigned int fork_count;
    unsigned int join_count;
    struct wined3d_shader_phase * fork;
    unsigned int fork_size;
    struct wined3d_shader_phase * join;
    unsigned int join_size;
};
struct wined3d_hull_shader {
    struct anon_6 phases;
    unsigned int output_vertex_count;
    int tessellator_output_primitive;
    int tessellator_partitioning;
};
struct wined3d_domain_shader {
    int tessellator_domain;
};
struct wined3d_geometry_shader {
    int input_type;
    int output_type;
    unsigned int vertices_out;
    unsigned int instance_count;
    struct wined3d_stream_output_desc * so_desc;
};
struct wined3d_pixel_shader {
    unsigned int input_reg_map[32];
    unsigned int input_reg_used;
    unsigned int declared_in_count;
    int color0_mov;
    unsigned int color0_reg;
    int force_early_depth_stencil;
    int depth_output;
    unsigned int interpolation_mode[3];
};
struct wined3d_shader_thread_group_size {
    unsigned int x;
    unsigned int y;
    unsigned int z;
};
struct wined3d_compute_shader {
    struct wined3d_shader_thread_group_size thread_group_size;
};
union anon_5 {
    struct wined3d_vertex_shader vs;
    struct wined3d_hull_shader hs;
    struct wined3d_domain_shader ds;
    struct wined3d_geometry_shader gs;
    struct wined3d_pixel_shader ps;
    struct wined3d_compute_shader cs;
};
struct wined3d_shader {
    int ref;
    struct wined3d_shader_limits * limits;
    void * function;
    unsigned int functionLength;
    void * byte_code;
    unsigned int byte_code_size;
    unsigned char load_local_constsF;
    unsigned char is_ffp_vs;
    unsigned char is_ffp_ps;
    int source_type;
    struct wined3d_shader_frontend * frontend;
    void * frontend_data;
    void * backend_data;
    void * parent;
    struct wined3d_parent_ops * parent_ops;
    struct list linked_programs;
    struct list constantsB;
    struct list constantsF;
    struct list constantsI;
    struct wined3d_shader_reg_maps reg_maps;
    int lconst_inf_or_nan;
    struct wined3d_shader_signature input_signature;
    struct wined3d_shader_signature output_signature;
    struct wined3d_shader_signature patch_constant_signature;
    struct wined3d_device * device;
    struct list shader_list_entry;
    union anon_5 u;
};
struct wined3d_vertex_declaration {
    int ref;
    void * parent;
    struct wined3d_parent_ops * parent_ops;
    struct wined3d_device * device;
    struct wined3d_vertex_declaration_element * elements;
    unsigned int element_count;
    unsigned char position_transformed;
    unsigned char point_size;
    unsigned char diffuse;
    unsigned char specular;
    unsigned char normal;
    unsigned char texcoords;
};
struct wined3d_rendertarget_view {
    int refcount;
    struct wined3d_resource * resource;
    void * parent;
    struct wined3d_parent_ops * parent_ops;
    struct wined3d_format * format;
    unsigned int format_attrs;
    unsigned int format_caps;
    unsigned int sub_resource_idx;
    unsigned int layer_count;
    unsigned int width;
    unsigned int height;
    struct wined3d_view_desc desc;
};













enum vkd3d_shader_source_type { VKD3D_SHADER_SOURCE_NONE = 0, VKD3D_SHADER_SOURCE_DXBC_TPF = 1, VKD3D_SHADER_SOURCE_HLSL = 2, VKD3D_SHADER_SOURCE_D3D_BYTECODE = 3, VKD3D_SHADER_SOURCE_DXBC_DXIL = 4, VKD3D_SHADER_SOURCE_FX = 5, VKD3D_SHADER_SOURCE_TX = 6, VKD3D_SHADER_SOURCE_TYPE_FORCE_32BIT = 0 };
enum _D3DDDIFORMAT { D3DDDIFMT_UNKNOWN = 0, D3DDDIFMT_R8G8B8 = 20, D3DDDIFMT_A8R8G8B8 = 21, D3DDDIFMT_X8R8G8B8 = 22, D3DDDIFMT_R5G6B5 = 23, D3DDDIFMT_X1R5G5B5 = 24, D3DDDIFMT_A1R5G5B5 = 25, D3DDDIFMT_A4R4G4B4 = 26, D3DDDIFMT_R3G3B2 = 27, D3DDDIFMT_A8 = 28, D3DDDIFMT_A8R3G3B2 = 29, D3DDDIFMT_X4R4G4B4 = 30, D3DDDIFMT_A2B10G10R10 = 31, D3DDDIFMT_A8B8G8R8 = 32, D3DDDIFMT_X8B8G8R8 = 33, D3DDDIFMT_G16R16 = 34, D3DDDIFMT_A2R10G10B10 = 35, D3DDDIFMT_A16B16G16R16 = 36, D3DDDIFMT_A8P8 = 40, D3DDDIFMT_P8 = 41, D3DDDIFMT_L8 = 50, D3DDDIFMT_A8L8 = 51, D3DDDIFMT_A4L4 = 52, D3DDDIFMT_V8U8 = 60, D3DDDIFMT_L6V5U5 = 61, D3DDDIFMT_X8L8V8U8 = 62, D3DDDIFMT_Q8W8V8U8 = 63, D3DDDIFMT_V16U16 = 64, D3DDDIFMT_W11V11U10 = 65, D3DDDIFMT_A2W10V10U10 = 67, D3DDDIFMT_D16_LOCKABLE = 70, D3DDDIFMT_D32 = 71, D3DDDIFMT_S1D15 = 72, D3DDDIFMT_D15S1 = 73, D3DDDIFMT_S8D24 = 74, D3DDDIFMT_D24S8 = 75, D3DDDIFMT_X8D24 = 76, D3DDDIFMT_D24X8 = 77, D3DDDIFMT_X4S4D24 = 78, D3DDDIFMT_D24X4S4 = 79, D3DDDIFMT_D16 = 80, D3DDDIFMT_L16 = 81, D3DDDIFMT_D32F_LOCKABLE = 82, D3DDDIFMT_D24FS8 = 83, D3DDDIFMT_D32_LOCKABLE = 84, D3DDDIFMT_S8_LOCKABLE = 85, D3DDDIFMT_G8R8 = 91, D3DDDIFMT_R8 = 92, D3DDDIFMT_VERTEXDATA = 100, D3DDDIFMT_INDEX16 = 101, D3DDDIFMT_INDEX32 = 102, D3DDDIFMT_Q16W16V16U16 = 110, D3DDDIFMT_R16F = 111, D3DDDIFMT_G16R16F = 112, D3DDDIFMT_A16B16G16R16F = 113, D3DDDIFMT_R32F = 114, D3DDDIFMT_G32R32F = 115, D3DDDIFMT_A32B32G32R32F = 116, D3DDDIFMT_CxV8U8 = 117, D3DDDIFMT_A1 = 118, D3DDDIFMT_A2B10G10R10_XR_BIAS = 119, D3DDDIFMT_DXVACOMPBUFFER_BASE = 150, D3DDDIFMT_PICTUREPARAMSDATA = 150, D3DDDIFMT_MACROBLOCKDATA = 151, D3DDDIFMT_RESIDUALDIFFERENCEDATA = 152, D3DDDIFMT_DEBLOCKINGDATA = 153, D3DDDIFMT_INVERSEQUANTIZATIONDATA = 154, D3DDDIFMT_SLICECONTROLDATA = 155, D3DDDIFMT_BITSTREAMDATA = 156, D3DDDIFMT_MOTIONVECTORBUFFER = 157, D3DDDIFMT_FILMGRAINBUFFER = 158, D3DDDIFMT_DXVA_RESERVED9 = 159, D3DDDIFMT_DXVA_RESERVED10 = 160, D3DDDIFMT_DXVA_RESERVED11 = 161, D3DDDIFMT_DXVA_RESERVED12 = 162, D3DDDIFMT_DXVA_RESERVED13 = 163, D3DDDIFMT_DXVA_RESERVED14 = 164, D3DDDIFMT_DXVA_RESERVED15 = 165, D3DDDIFMT_DXVA_RESERVED16 = 166, D3DDDIFMT_DXVA_RESERVED17 = 167, D3DDDIFMT_DXVA_RESERVED18 = 168, D3DDDIFMT_DXVA_RESERVED19 = 169, D3DDDIFMT_DXVA_RESERVED20 = 170, D3DDDIFMT_DXVA_RESERVED21 = 171, D3DDDIFMT_DXVA_RESERVED22 = 172, D3DDDIFMT_DXVA_RESERVED23 = 173, D3DDDIFMT_DXVA_RESERVED24 = 174, D3DDDIFMT_DXVA_RESERVED25 = 175, D3DDDIFMT_DXVA_RESERVED26 = 176, D3DDDIFMT_DXVA_RESERVED27 = 177, D3DDDIFMT_DXVA_RESERVED28 = 178, D3DDDIFMT_DXVA_RESERVED29 = 179, D3DDDIFMT_DXVA_RESERVED30 = 180, D3DDDIFMT_DXVA_RESERVED31 = 181, D3DDDIFMT_DXVACOMPBUFFER_MAX = 181, D3DDDIFMT_BINARYBUFFER = 199, D3DDDIFMT_DXT1 = 0, D3DDDIFMT_DXT2 = 0, D3DDDIFMT_DXT3 = 0, D3DDDIFMT_DXT4 = 0, D3DDDIFMT_DXT5 = 0, D3DDDIFMT_G8R8_G8B8 = 0, D3DDDIFMT_MULTI2_ARGB8 = 0, D3DDDIFMT_R8G8_B8G8 = 0, D3DDDIFMT_UYVY = 0, D3DDDIFMT_YUY2 = 0, D3DDDIFMT_FORCE_UINT = 0 };
enum _D3DKMT_QUERYRESULT_PREEMPTION_ATTEMPT_RESULT { D3DKMT_PreemptionAttempt = 0, D3DKMT_PreemptionAttemptSuccess = 1, D3DKMT_PreemptionAttemptMissNoCommand = 2, D3DKMT_PreemptionAttemptMissNotEnabled = 3, D3DKMT_PreemptionAttemptMissNextFence = 4, D3DKMT_PreemptionAttemptMissPagingCommand = 5, D3DKMT_PreemptionAttemptMissSplittedCommand = 6, D3DKMT_PreemptionAttemptMissFenceCommand = 7, D3DKMT_PreemptionAttemptMissRenderPendingFlip = 8, D3DKMT_PreemptionAttemptMissNotMakingProgress = 9, D3DKMT_PreemptionAttemptMissLessPriority = 10, D3DKMT_PreemptionAttemptMissRemainingQuantum = 11, D3DKMT_PreemptionAttemptMissRemainingPreemptionQuantum = 12, D3DKMT_PreemptionAttemptMissAlreadyPreempting = 13, D3DKMT_PreemptionAttemptMissGlobalBlock = 14, D3DKMT_PreemptionAttemptMissAlreadyRunning = 15, D3DKMT_PreemptionAttemptStatisticsMax = 16 };
enum _D3DKMT_QUERYSTATISTICS_ALLOCATION_PRIORITY_CLASS { D3DKMT_AllocationPriorityClassMinimum = 0, D3DKMT_AllocationPriorityClassLow = 1, D3DKMT_AllocationPriorityClassNormal = 2, D3DKMT_AllocationPriorityClassHigh = 3, D3DKMT_AllocationPriorityClassMaximum = 4, D3DKMT_MaxAllocationPriorityClass = 5 };
enum _D3DKMT_QUERYSTATISTICS_QUEUE_PACKET_TYPE { D3DKMT_RenderCommandBuffer = 0, D3DKMT_DeferredCommandBuffer = 1, D3DKMT_SystemCommandBuffer = 2, D3DKMT_MmIoFlipCommandBuffer = 3, D3DKMT_WaitCommandBuffer = 4, D3DKMT_SignalCommandBuffer = 5, D3DKMT_DeviceCommandBuffer = 6, D3DKMT_SoftwareCommandBuffer = 7, D3DKMT_QueuePacketTypeMax = 8 };
enum _D3DKMT_QUERYSTATISTICS_DMA_PACKET_TYPE { D3DKMT_ClientRenderBuffer = 0, D3DKMT_ClientPagingBuffer = 1, D3DKMT_SystemPagingBuffer = 2, D3DKMT_SystemPreemptionBuffer = 3, D3DKMT_DmaPacketTypeMax = 4 };
enum __wine_debug_class { __WINE_DBCL_FIXME = 0, __WINE_DBCL_ERR = 1, __WINE_DBCL_WARN = 2, __WINE_DBCL_TRACE = 3, __WINE_DBCL_INIT = 7 };
enum VARENUM { VT_EMPTY = 0, VT_NULL = 1, VT_I2 = 2, VT_I4 = 3, VT_R4 = 4, VT_R8 = 5, VT_CY = 6, VT_DATE = 7, VT_BSTR = 8, VT_DISPATCH = 9, VT_ERROR = 10, VT_BOOL = 11, VT_VARIANT = 12, VT_UNKNOWN = 13, VT_DECIMAL = 14, VT_I1 = 16, VT_UI1 = 17, VT_UI2 = 18, VT_UI4 = 19, VT_I8 = 20, VT_UI8 = 21, VT_INT = 22, VT_UINT = 23, VT_VOID = 24, VT_HRESULT = 25, VT_PTR = 26, VT_SAFEARRAY = 27, VT_CARRAY = 28, VT_USERDEFINED = 29, VT_LPSTR = 30, VT_LPWSTR = 31, VT_RECORD = 36, VT_INT_PTR = 37, VT_UINT_PTR = 38, VT_FILETIME = 64, VT_BLOB = 65, VT_STREAM = 66, VT_STORAGE = 67, VT_STREAMED_OBJECT = 68, VT_STORED_OBJECT = 69, VT_BLOB_OBJECT = 70, VT_CF = 71, VT_CLSID = 72, VT_VERSIONED_STREAM = 73, VT_BSTR_BLOB = 4095, VT_VECTOR = 4096, VT_ARRAY = 8192, VT_BYREF = 16384, VT_RESERVED = 32768, VT_ILLEGAL = 65535, VT_ILLEGALMASKED = 4095, VT_TYPEMASK = 4095 };
enum wined3d_light_type { WINED3D_LIGHT_POINT = 1, WINED3D_LIGHT_SPOT = 2, WINED3D_LIGHT_DIRECTIONAL = 3, WINED3D_LIGHT_PARALLELPOINT = 4, WINED3D_LIGHT_GLSPOT = 5 };
enum wined3d_primitive_type { WINED3D_PT_UNDEFINED = 0, WINED3D_PT_POINTLIST = 1, WINED3D_PT_LINELIST = 2, WINED3D_PT_LINESTRIP = 3, WINED3D_PT_TRIANGLELIST = 4, WINED3D_PT_TRIANGLESTRIP = 5, WINED3D_PT_TRIANGLEFAN = 6, WINED3D_PT_LINELIST_ADJ = 10, WINED3D_PT_LINESTRIP_ADJ = 11, WINED3D_PT_TRIANGLELIST_ADJ = 12, WINED3D_PT_TRIANGLESTRIP_ADJ = 13, WINED3D_PT_PATCH = 14 };
enum wined3d_device_type { WINED3D_DEVICE_TYPE_HAL = 1, WINED3D_DEVICE_TYPE_REF = 2, WINED3D_DEVICE_TYPE_SW = 3, WINED3D_DEVICE_TYPE_NULLREF = 4 };
enum wined3d_feature_level { WINED3D_FEATURE_LEVEL_NONE = 0, WINED3D_FEATURE_LEVEL_5 = 20480, WINED3D_FEATURE_LEVEL_6 = 24576, WINED3D_FEATURE_LEVEL_7 = 28672, WINED3D_FEATURE_LEVEL_8 = 32768, WINED3D_FEATURE_LEVEL_9_1 = 37120, WINED3D_FEATURE_LEVEL_9_2 = 37376, WINED3D_FEATURE_LEVEL_9_3 = 37632, WINED3D_FEATURE_LEVEL_10 = 40960, WINED3D_FEATURE_LEVEL_10_1 = 41216, WINED3D_FEATURE_LEVEL_11 = 45056, WINED3D_FEATURE_LEVEL_11_1 = 45312 };
enum wined3d_format_id { WINED3DFMT_UNKNOWN = 0, WINED3DFMT_B8G8R8_UNORM = 1, WINED3DFMT_B5G5R5X1_UNORM = 2, WINED3DFMT_B4G4R4A4_UNORM = 3, WINED3DFMT_B2G3R3_UNORM = 4, WINED3DFMT_B2G3R3A8_UNORM = 5, WINED3DFMT_B4G4R4X4_UNORM = 6, WINED3DFMT_R8G8B8X8_UNORM = 7, WINED3DFMT_B10G10R10A2_UNORM = 8, WINED3DFMT_P8_UINT_A8_UNORM = 9, WINED3DFMT_P8_UINT = 10, WINED3DFMT_L8_UNORM = 11, WINED3DFMT_L8A8_UNORM = 12, WINED3DFMT_L4A4_UNORM = 13, WINED3DFMT_R5G5_SNORM_L6_UNORM = 14, WINED3DFMT_R8G8_SNORM_L8X8_UNORM = 15, WINED3DFMT_R10G11B11_SNORM = 16, WINED3DFMT_R10G10B10X2_TYPELESS = 17, WINED3DFMT_R10G10B10X2_UINT = 18, WINED3DFMT_R10G10B10X2_SNORM = 19, WINED3DFMT_R10G10B10_SNORM_A2_UNORM = 20, WINED3DFMT_D16_LOCKABLE = 21, WINED3DFMT_D32_UNORM = 22, WINED3DFMT_S1_UINT_D15_UNORM = 23, WINED3DFMT_X8D24_UNORM = 24, WINED3DFMT_S4X4_UINT_D24_UNORM = 25, WINED3DFMT_L16_UNORM = 26, WINED3DFMT_S8_UINT_D24_FLOAT = 27, WINED3DFMT_R8G8_SNORM_Cx = 28, WINED3DFMT_R32G32B32A32_TYPELESS = 29, WINED3DFMT_R32G32B32A32_FLOAT = 30, WINED3DFMT_R32G32B32A32_UINT = 31, WINED3DFMT_R32G32B32A32_SINT = 32, WINED3DFMT_R32G32B32_TYPELESS = 33, WINED3DFMT_R32G32B32_FLOAT = 34, WINED3DFMT_R32G32B32_UINT = 35, WINED3DFMT_R32G32B32_SINT = 36, WINED3DFMT_R16G16B16A16_TYPELESS = 37, WINED3DFMT_R16G16B16A16_FLOAT = 38, WINED3DFMT_R16G16B16A16_UNORM = 39, WINED3DFMT_R16G16B16A16_UINT = 40, WINED3DFMT_R16G16B16A16_SNORM = 41, WINED3DFMT_R16G16B16A16_SINT = 42, WINED3DFMT_R32G32_TYPELESS = 43, WINED3DFMT_R32G32_FLOAT = 44, WINED3DFMT_R32G32_UINT = 45, WINED3DFMT_R32G32_SINT = 46, WINED3DFMT_R32G8X24_TYPELESS = 47, WINED3DFMT_D32_FLOAT_S8X24_UINT = 48, WINED3DFMT_R32_FLOAT_X8X24_TYPELESS = 49, WINED3DFMT_X32_TYPELESS_G8X24_UINT = 50, WINED3DFMT_R10G10B10A2_TYPELESS = 51, WINED3DFMT_R10G10B10A2_UNORM = 52, WINED3DFMT_R10G10B10A2_UINT = 53, WINED3DFMT_R10G10B10A2_SNORM = 54, WINED3DFMT_R10G10B10_XR_BIAS_A2_UNORM = 55, WINED3DFMT_R11G11B10_FLOAT = 56, WINED3DFMT_R8G8B8A8_TYPELESS = 57, WINED3DFMT_R8G8B8A8_UNORM = 58, WINED3DFMT_R8G8B8A8_UNORM_SRGB = 59, WINED3DFMT_R8G8B8A8_UINT = 60, WINED3DFMT_R8G8B8A8_SNORM = 61, WINED3DFMT_R8G8B8A8_SINT = 62, WINED3DFMT_R16G16_TYPELESS = 63, WINED3DFMT_R16G16_FLOAT = 64, WINED3DFMT_R16G16_UNORM = 65, WINED3DFMT_R16G16_UINT = 66, WINED3DFMT_R16G16_SNORM = 67, WINED3DFMT_R16G16_SINT = 68, WINED3DFMT_R32_TYPELESS = 69, WINED3DFMT_D32_FLOAT = 70, WINED3DFMT_R32_FLOAT = 71, WINED3DFMT_R32_UINT = 72, WINED3DFMT_R32_SINT = 73, WINED3DFMT_R24G8_TYPELESS = 74, WINED3DFMT_D24_UNORM_S8_UINT = 75, WINED3DFMT_R24_UNORM_X8_TYPELESS = 76, WINED3DFMT_X24_TYPELESS_G8_UINT = 77, WINED3DFMT_R8G8_TYPELESS = 78, WINED3DFMT_R8G8_UNORM = 79, WINED3DFMT_R8G8_UINT = 80, WINED3DFMT_R8G8_SNORM = 81, WINED3DFMT_R8G8_SINT = 82, WINED3DFMT_R16_TYPELESS = 83, WINED3DFMT_R16_FLOAT = 84, WINED3DFMT_D16_UNORM = 85, WINED3DFMT_R16_UNORM = 86, WINED3DFMT_R16_UINT = 87, WINED3DFMT_R16_SNORM = 88, WINED3DFMT_R16_SINT = 89, WINED3DFMT_R8_TYPELESS = 90, WINED3DFMT_R8_UNORM = 91, WINED3DFMT_R8_UINT = 92, WINED3DFMT_R8_SNORM = 93, WINED3DFMT_R8_SINT = 94, WINED3DFMT_A8_UNORM = 95, WINED3DFMT_R1_UNORM = 96, WINED3DFMT_R9G9B9E5_SHAREDEXP = 97, WINED3DFMT_R8G8_B8G8_UNORM = 98, WINED3DFMT_G8R8_G8B8_UNORM = 99, WINED3DFMT_NV12_PLANAR = 100, WINED3DFMT_BC1_TYPELESS = 101, WINED3DFMT_BC1_UNORM = 102, WINED3DFMT_BC1_UNORM_SRGB = 103, WINED3DFMT_BC2_TYPELESS = 104, WINED3DFMT_BC2_UNORM = 105, WINED3DFMT_BC2_UNORM_SRGB = 106, WINED3DFMT_BC3_TYPELESS = 107, WINED3DFMT_BC3_UNORM = 108, WINED3DFMT_BC3_UNORM_SRGB = 109, WINED3DFMT_BC4_TYPELESS = 110, WINED3DFMT_BC4_UNORM = 111, WINED3DFMT_BC4_SNORM = 112, WINED3DFMT_BC5_TYPELESS = 113, WINED3DFMT_BC5_UNORM = 114, WINED3DFMT_BC5_SNORM = 115, WINED3DFMT_B5G6R5_UNORM = 116, WINED3DFMT_B5G5R5A1_UNORM = 117, WINED3DFMT_B8G8R8A8_UNORM = 118, WINED3DFMT_B8G8R8X8_UNORM = 119, WINED3DFMT_B8G8R8A8_TYPELESS = 120, WINED3DFMT_B8G8R8A8_UNORM_SRGB = 121, WINED3DFMT_B8G8R8X8_TYPELESS = 122, WINED3DFMT_B8G8R8X8_UNORM_SRGB = 123, WINED3DFMT_BC6H_TYPELESS = 124, WINED3DFMT_BC6H_UF16 = 125, WINED3DFMT_BC6H_SF16 = 126, WINED3DFMT_BC7_TYPELESS = 127, WINED3DFMT_BC7_UNORM = 128, WINED3DFMT_BC7_UNORM_SRGB = 129, WINED3DFMT_UYVY = 0, WINED3DFMT_YUY2 = 0, WINED3DFMT_YV12 = 0, WINED3DFMT_DXT1 = 0, WINED3DFMT_DXT2 = 0, WINED3DFMT_DXT3 = 0, WINED3DFMT_DXT4 = 0, WINED3DFMT_DXT5 = 0, WINED3DFMT_MULTI2_ARGB8 = 0, WINED3DFMT_G8R8_G8B8 = 0, WINED3DFMT_R8G8_B8G8 = 0, WINED3DFMT_ATI1N = 0, WINED3DFMT_ATI2N = 0, WINED3DFMT_INST = 0, WINED3DFMT_NVDB = 0, WINED3DFMT_NVHU = 0, WINED3DFMT_NVHS = 0, WINED3DFMT_INTZ = 0, WINED3DFMT_RESZ = 0, WINED3DFMT_NULL = 0, WINED3DFMT_R16 = 0, WINED3DFMT_AL16 = 0, WINED3DFMT_NV12 = 0, WINED3DFMT_DF16 = 0, WINED3DFMT_DF24 = 0, WINED3DFMT_ATOC = 0, WINED3DFMT_FORCE_DWORD = 0 };
enum wined3d_render_state { WINED3D_RS_ANTIALIAS = 2, WINED3D_RS_TEXTUREPERSPECTIVE = 4, WINED3D_RS_WRAPU = 5, WINED3D_RS_WRAPV = 6, WINED3D_RS_ZENABLE = 7, WINED3D_RS_FILLMODE = 8, WINED3D_RS_SHADEMODE = 9, WINED3D_RS_LINEPATTERN = 10, WINED3D_RS_MONOENABLE = 11, WINED3D_RS_ROP2 = 12, WINED3D_RS_PLANEMASK = 13, WINED3D_RS_ZWRITEENABLE = 14, WINED3D_RS_ALPHATESTENABLE = 15, WINED3D_RS_LASTPIXEL = 16, WINED3D_RS_SRCBLEND = 19, WINED3D_RS_DESTBLEND = 20, WINED3D_RS_CULLMODE = 22, WINED3D_RS_ZFUNC = 23, WINED3D_RS_ALPHAREF = 24, WINED3D_RS_ALPHAFUNC = 25, WINED3D_RS_DITHERENABLE = 26, WINED3D_RS_ALPHABLENDENABLE = 27, WINED3D_RS_FOGENABLE = 28, WINED3D_RS_SPECULARENABLE = 29, WINED3D_RS_ZVISIBLE = 30, WINED3D_RS_SUBPIXEL = 31, WINED3D_RS_SUBPIXELX = 32, WINED3D_RS_STIPPLEDALPHA = 33, WINED3D_RS_FOGCOLOR = 34, WINED3D_RS_FOGTABLEMODE = 35, WINED3D_RS_FOGSTART = 36, WINED3D_RS_FOGEND = 37, WINED3D_RS_FOGDENSITY = 38, WINED3D_RS_STIPPLEENABLE = 39, WINED3D_RS_COLORKEYENABLE = 41, WINED3D_RS_MIPMAPLODBIAS = 46, WINED3D_RS_RANGEFOGENABLE = 48, WINED3D_RS_ANISOTROPY = 49, WINED3D_RS_FLUSHBATCH = 50, WINED3D_RS_TRANSLUCENTSORTINDEPENDENT = 51, WINED3D_RS_STENCILENABLE = 52, WINED3D_RS_STENCILFAIL = 53, WINED3D_RS_STENCILZFAIL = 54, WINED3D_RS_STENCILPASS = 55, WINED3D_RS_STENCILFUNC = 56, WINED3D_RS_STENCILREF = 57, WINED3D_RS_STENCILMASK = 58, WINED3D_RS_STENCILWRITEMASK = 59, WINED3D_RS_TEXTUREFACTOR = 60, WINED3D_RS_WRAP0 = 128, WINED3D_RS_WRAP1 = 129, WINED3D_RS_WRAP2 = 130, WINED3D_RS_WRAP3 = 131, WINED3D_RS_WRAP4 = 132, WINED3D_RS_WRAP5 = 133, WINED3D_RS_WRAP6 = 134, WINED3D_RS_WRAP7 = 135, WINED3D_RS_CLIPPING = 136, WINED3D_RS_LIGHTING = 137, WINED3D_RS_EXTENTS = 138, WINED3D_RS_AMBIENT = 139, WINED3D_RS_FOGVERTEXMODE = 140, WINED3D_RS_COLORVERTEX = 141, WINED3D_RS_LOCALVIEWER = 142, WINED3D_RS_NORMALIZENORMALS = 143, WINED3D_RS_COLORKEYBLENDENABLE = 144, WINED3D_RS_DIFFUSEMATERIALSOURCE = 145, WINED3D_RS_SPECULARMATERIALSOURCE = 146, WINED3D_RS_AMBIENTMATERIALSOURCE = 147, WINED3D_RS_EMISSIVEMATERIALSOURCE = 148, WINED3D_RS_VERTEXBLEND = 151, WINED3D_RS_CLIPPLANEENABLE = 152, WINED3D_RS_SOFTWAREVERTEXPROCESSING = 153, WINED3D_RS_POINTSIZE = 154, WINED3D_RS_POINTSIZE_MIN = 155, WINED3D_RS_POINTSPRITEENABLE = 156, WINED3D_RS_POINTSCALEENABLE = 157, WINED3D_RS_POINTSCALE_A = 158, WINED3D_RS_POINTSCALE_B = 159, WINED3D_RS_POINTSCALE_C = 160, WINED3D_RS_MULTISAMPLEANTIALIAS = 161, WINED3D_RS_MULTISAMPLEMASK = 162, WINED3D_RS_PATCHEDGESTYLE = 163, WINED3D_RS_PATCHSEGMENTS = 164, WINED3D_RS_DEBUGMONITORTOKEN = 165, WINED3D_RS_POINTSIZE_MAX = 166, WINED3D_RS_INDEXEDVERTEXBLENDENABLE = 167, WINED3D_RS_COLORWRITEENABLE = 168, WINED3D_RS_TWEENFACTOR = 170, WINED3D_RS_BLENDOP = 171, WINED3D_RS_POSITIONDEGREE = 172, WINED3D_RS_NORMALDEGREE = 173, WINED3D_RS_SCISSORTESTENABLE = 174, WINED3D_RS_SLOPESCALEDEPTHBIAS = 175, WINED3D_RS_ANTIALIASEDLINEENABLE = 176, WINED3D_RS_MINTESSELLATIONLEVEL = 178, WINED3D_RS_MAXTESSELLATIONLEVEL = 179, WINED3D_RS_ADAPTIVETESS_X = 180, WINED3D_RS_ADAPTIVETESS_Y = 181, WINED3D_RS_ADAPTIVETESS_Z = 182, WINED3D_RS_ADAPTIVETESS_W = 183, WINED3D_RS_ENABLEADAPTIVETESSELLATION = 184, WINED3D_RS_TWOSIDEDSTENCILMODE = 185, WINED3D_RS_BACK_STENCILFAIL = 186, WINED3D_RS_BACK_STENCILZFAIL = 187, WINED3D_RS_BACK_STENCILPASS = 188, WINED3D_RS_BACK_STENCILFUNC = 189, WINED3D_RS_COLORWRITEENABLE1 = 190, WINED3D_RS_COLORWRITEENABLE2 = 191, WINED3D_RS_COLORWRITEENABLE3 = 192, WINED3D_RS_BLENDFACTOR = 193, WINED3D_RS_SRGBWRITEENABLE = 194, WINED3D_RS_DEPTHBIAS = 195, WINED3D_RS_WRAP8 = 198, WINED3D_RS_WRAP9 = 199, WINED3D_RS_WRAP10 = 200, WINED3D_RS_WRAP11 = 201, WINED3D_RS_WRAP12 = 202, WINED3D_RS_WRAP13 = 203, WINED3D_RS_WRAP14 = 204, WINED3D_RS_WRAP15 = 205, WINED3D_RS_SEPARATEALPHABLENDENABLE = 206, WINED3D_RS_SRCBLENDALPHA = 207, WINED3D_RS_DESTBLENDALPHA = 208, WINED3D_RS_BLENDOPALPHA = 209 };
enum wined3d_blend { WINED3D_BLEND_ZERO = 1, WINED3D_BLEND_ONE = 2, WINED3D_BLEND_SRCCOLOR = 3, WINED3D_BLEND_INVSRCCOLOR = 4, WINED3D_BLEND_SRCALPHA = 5, WINED3D_BLEND_INVSRCALPHA = 6, WINED3D_BLEND_DESTALPHA = 7, WINED3D_BLEND_INVDESTALPHA = 8, WINED3D_BLEND_DESTCOLOR = 9, WINED3D_BLEND_INVDESTCOLOR = 10, WINED3D_BLEND_SRCALPHASAT = 11, WINED3D_BLEND_BOTHSRCALPHA = 12, WINED3D_BLEND_BOTHINVSRCALPHA = 13, WINED3D_BLEND_BLENDFACTOR = 14, WINED3D_BLEND_INVBLENDFACTOR = 15, WINED3D_BLEND_SRC1COLOR = 16, WINED3D_BLEND_INVSRC1COLOR = 17, WINED3D_BLEND_SRC1ALPHA = 18, WINED3D_BLEND_INVSRC1ALPHA = 19 };
enum wined3d_blend_op { WINED3D_BLEND_OP_ADD = 1, WINED3D_BLEND_OP_SUBTRACT = 2, WINED3D_BLEND_OP_REVSUBTRACT = 3, WINED3D_BLEND_OP_MIN = 4, WINED3D_BLEND_OP_MAX = 5 };
enum wined3d_vertex_blend_flags { WINED3D_VBF_DISABLE = 0, WINED3D_VBF_1WEIGHTS = 1, WINED3D_VBF_2WEIGHTS = 2, WINED3D_VBF_3WEIGHTS = 3, WINED3D_VBF_TWEENING = 255, WINED3D_VBF_0WEIGHTS = 256 };
enum wined3d_cmp_func { WINED3D_CMP_NEVER = 1, WINED3D_CMP_LESS = 2, WINED3D_CMP_EQUAL = 3, WINED3D_CMP_LESSEQUAL = 4, WINED3D_CMP_GREATER = 5, WINED3D_CMP_NOTEQUAL = 6, WINED3D_CMP_GREATEREQUAL = 7, WINED3D_CMP_ALWAYS = 8 };
enum wined3d_filter_reduction_mode { WINED3D_FILTER_REDUCTION_WEIGHTED_AVERAGE = 0, WINED3D_FILTER_REDUCTION_COMPARISON = 1, WINED3D_FILTER_REDUCTION_MINIMUM = 2, WINED3D_FILTER_REDUCTION_MAXIMUM = 3 };
enum wined3d_fog_mode { WINED3D_FOG_NONE = 0, WINED3D_FOG_EXP = 1, WINED3D_FOG_EXP2 = 2, WINED3D_FOG_LINEAR = 3 };
enum wined3d_fill_mode { WINED3D_FILL_POINT = 1, WINED3D_FILL_WIREFRAME = 2, WINED3D_FILL_SOLID = 3 };
enum wined3d_cull { WINED3D_CULL_NONE = 1, WINED3D_CULL_FRONT = 2, WINED3D_CULL_BACK = 3 };
enum wined3d_stencil_op { WINED3D_STENCIL_OP_KEEP = 1, WINED3D_STENCIL_OP_ZERO = 2, WINED3D_STENCIL_OP_REPLACE = 3, WINED3D_STENCIL_OP_INCR_SAT = 4, WINED3D_STENCIL_OP_DECR_SAT = 5, WINED3D_STENCIL_OP_INVERT = 6, WINED3D_STENCIL_OP_INCR = 7, WINED3D_STENCIL_OP_DECR = 8 };
enum wined3d_material_color_source { WINED3D_MCS_MATERIAL = 0, WINED3D_MCS_COLOR1 = 1, WINED3D_MCS_COLOR2 = 2 };
enum wined3d_swap_effect { WINED3D_SWAP_EFFECT_DISCARD = 0, WINED3D_SWAP_EFFECT_SEQUENTIAL = 1, WINED3D_SWAP_EFFECT_FLIP_DISCARD = 2, WINED3D_SWAP_EFFECT_FLIP_SEQUENTIAL = 3, WINED3D_SWAP_EFFECT_COPY = 4, WINED3D_SWAP_EFFECT_COPY_VSYNC = 5, WINED3D_SWAP_EFFECT_OVERLAY = 6 };
enum wined3d_sampler_state { WINED3D_SAMP_ADDRESS_U = 1, WINED3D_SAMP_ADDRESS_V = 2, WINED3D_SAMP_ADDRESS_W = 3, WINED3D_SAMP_BORDER_COLOR = 4, WINED3D_SAMP_MAG_FILTER = 5, WINED3D_SAMP_MIN_FILTER = 6, WINED3D_SAMP_MIP_FILTER = 7, WINED3D_SAMP_MIPMAP_LOD_BIAS = 8, WINED3D_SAMP_MAX_MIP_LEVEL = 9, WINED3D_SAMP_MAX_ANISOTROPY = 10, WINED3D_SAMP_SRGB_TEXTURE = 11, WINED3D_SAMP_ELEMENT_INDEX = 12, WINED3D_SAMP_DMAP_OFFSET = 13 };
enum wined3d_multisample_type { WINED3D_MULTISAMPLE_NONE = 0, WINED3D_MULTISAMPLE_NON_MASKABLE = 1, WINED3D_MULTISAMPLE_2_SAMPLES = 2, WINED3D_MULTISAMPLE_3_SAMPLES = 3, WINED3D_MULTISAMPLE_4_SAMPLES = 4, WINED3D_MULTISAMPLE_5_SAMPLES = 5, WINED3D_MULTISAMPLE_6_SAMPLES = 6, WINED3D_MULTISAMPLE_7_SAMPLES = 7, WINED3D_MULTISAMPLE_8_SAMPLES = 8, WINED3D_MULTISAMPLE_9_SAMPLES = 9, WINED3D_MULTISAMPLE_10_SAMPLES = 10, WINED3D_MULTISAMPLE_11_SAMPLES = 11, WINED3D_MULTISAMPLE_12_SAMPLES = 12, WINED3D_MULTISAMPLE_13_SAMPLES = 13, WINED3D_MULTISAMPLE_14_SAMPLES = 14, WINED3D_MULTISAMPLE_15_SAMPLES = 15, WINED3D_MULTISAMPLE_16_SAMPLES = 16 };
enum wined3d_texture_stage_state { WINED3D_TSS_COLOR_OP = 0, WINED3D_TSS_COLOR_ARG1 = 1, WINED3D_TSS_COLOR_ARG2 = 2, WINED3D_TSS_ALPHA_OP = 3, WINED3D_TSS_ALPHA_ARG1 = 4, WINED3D_TSS_ALPHA_ARG2 = 5, WINED3D_TSS_BUMPENV_MAT00 = 6, WINED3D_TSS_BUMPENV_MAT01 = 7, WINED3D_TSS_BUMPENV_MAT10 = 8, WINED3D_TSS_BUMPENV_MAT11 = 9, WINED3D_TSS_TEXCOORD_INDEX = 10, WINED3D_TSS_BUMPENV_LSCALE = 11, WINED3D_TSS_BUMPENV_LOFFSET = 12, WINED3D_TSS_TEXTURE_TRANSFORM_FLAGS = 13, WINED3D_TSS_COLOR_ARG0 = 14, WINED3D_TSS_ALPHA_ARG0 = 15, WINED3D_TSS_RESULT_ARG = 16, WINED3D_TSS_CONSTANT = 17, WINED3D_TSS_INVALID = 0 };
enum wined3d_texture_transform_flags { WINED3D_TTFF_DISABLE = 0, WINED3D_TTFF_COUNT1 = 1, WINED3D_TTFF_COUNT2 = 2, WINED3D_TTFF_COUNT3 = 3, WINED3D_TTFF_COUNT4 = 4, WINED3D_TTFF_PROJECTED = 256 };
enum wined3d_texture_op { WINED3D_TOP_DISABLE = 1, WINED3D_TOP_SELECT_ARG1 = 2, WINED3D_TOP_SELECT_ARG2 = 3, WINED3D_TOP_MODULATE = 4, WINED3D_TOP_MODULATE_2X = 5, WINED3D_TOP_MODULATE_4X = 6, WINED3D_TOP_ADD = 7, WINED3D_TOP_ADD_SIGNED = 8, WINED3D_TOP_ADD_SIGNED_2X = 9, WINED3D_TOP_SUBTRACT = 10, WINED3D_TOP_ADD_SMOOTH = 11, WINED3D_TOP_BLEND_DIFFUSE_ALPHA = 12, WINED3D_TOP_BLEND_TEXTURE_ALPHA = 13, WINED3D_TOP_BLEND_FACTOR_ALPHA = 14, WINED3D_TOP_BLEND_TEXTURE_ALPHA_PM = 15, WINED3D_TOP_BLEND_CURRENT_ALPHA = 16, WINED3D_TOP_PREMODULATE = 17, WINED3D_TOP_MODULATE_ALPHA_ADD_COLOR = 18, WINED3D_TOP_MODULATE_COLOR_ADD_ALPHA = 19, WINED3D_TOP_MODULATE_INVALPHA_ADD_COLOR = 20, WINED3D_TOP_MODULATE_INVCOLOR_ADD_ALPHA = 21, WINED3D_TOP_BUMPENVMAP = 22, WINED3D_TOP_BUMPENVMAP_LUMINANCE = 23, WINED3D_TOP_DOTPRODUCT3 = 24, WINED3D_TOP_MULTIPLY_ADD = 25, WINED3D_TOP_LERP = 26 };
enum wined3d_texture_address { WINED3D_TADDRESS_WRAP = 1, WINED3D_TADDRESS_MIRROR = 2, WINED3D_TADDRESS_CLAMP = 3, WINED3D_TADDRESS_BORDER = 4, WINED3D_TADDRESS_MIRROR_ONCE = 5 };
enum wined3d_transform_state { WINED3D_TS_VIEW = 2, WINED3D_TS_PROJECTION = 3, WINED3D_TS_TEXTURE0 = 16, WINED3D_TS_TEXTURE1 = 17, WINED3D_TS_TEXTURE2 = 18, WINED3D_TS_TEXTURE3 = 19, WINED3D_TS_TEXTURE4 = 20, WINED3D_TS_TEXTURE5 = 21, WINED3D_TS_TEXTURE6 = 22, WINED3D_TS_TEXTURE7 = 23, WINED3D_TS_WORLD = 256, WINED3D_TS_WORLD1 = 257, WINED3D_TS_WORLD2 = 258, WINED3D_TS_WORLD3 = 259 };
enum wined3d_texture_filter_type { WINED3D_TEXF_NONE = 0, WINED3D_TEXF_POINT = 1, WINED3D_TEXF_LINEAR = 2, WINED3D_TEXF_ANISOTROPIC = 3, WINED3D_TEXF_FLAT_CUBIC = 4, WINED3D_TEXF_GAUSSIAN_CUBIC = 5, WINED3D_TEXF_PYRAMIDAL_QUAD = 6, WINED3D_TEXF_GAUSSIAN_QUAD = 7 };
enum wined3d_resource_type { WINED3D_RTYPE_NONE = 0, WINED3D_RTYPE_BUFFER = 1, WINED3D_RTYPE_TEXTURE_1D = 2, WINED3D_RTYPE_TEXTURE_2D = 3, WINED3D_RTYPE_TEXTURE_3D = 4 };
enum wined3d_query_type { WINED3D_QUERY_TYPE_VCACHE = 4, WINED3D_QUERY_TYPE_RESOURCE_MANAGER = 5, WINED3D_QUERY_TYPE_VERTEX_STATS = 6, WINED3D_QUERY_TYPE_EVENT = 8, WINED3D_QUERY_TYPE_OCCLUSION = 9, WINED3D_QUERY_TYPE_TIMESTAMP = 10, WINED3D_QUERY_TYPE_TIMESTAMP_DISJOINT = 11, WINED3D_QUERY_TYPE_TIMESTAMP_FREQ = 12, WINED3D_QUERY_TYPE_PIPELINE_TIMINGS = 13, WINED3D_QUERY_TYPE_INTERFACE_TIMINGS = 14, WINED3D_QUERY_TYPE_VERTEX_TIMINGS = 15, WINED3D_QUERY_TYPE_PIXEL_TIMINGS = 16, WINED3D_QUERY_TYPE_BANDWIDTH_TIMINGS = 17, WINED3D_QUERY_TYPE_CACHE_UTILIZATION = 18, WINED3D_QUERY_TYPE_MEMORY_PRESSURE = 19, WINED3D_QUERY_TYPE_PIPELINE_STATISTICS = 20, WINED3D_QUERY_TYPE_SO_STATISTICS = 21, WINED3D_QUERY_TYPE_SO_OVERFLOW = 22, WINED3D_QUERY_TYPE_SO_STATISTICS_STREAM0 = 23, WINED3D_QUERY_TYPE_SO_STATISTICS_STREAM1 = 24, WINED3D_QUERY_TYPE_SO_STATISTICS_STREAM2 = 25, WINED3D_QUERY_TYPE_SO_STATISTICS_STREAM3 = 26, WINED3D_QUERY_TYPE_SO_OVERFLOW_STREAM0 = 27, WINED3D_QUERY_TYPE_SO_OVERFLOW_STREAM1 = 28, WINED3D_QUERY_TYPE_SO_OVERFLOW_STREAM2 = 29, WINED3D_QUERY_TYPE_SO_OVERFLOW_STREAM3 = 30 };
enum wined3d_decl_method { WINED3D_DECL_METHOD_DEFAULT = 0, WINED3D_DECL_METHOD_PARTIAL_U = 1, WINED3D_DECL_METHOD_PARTIAL_V = 2, WINED3D_DECL_METHOD_CROSS_UV = 3, WINED3D_DECL_METHOD_UV = 4, WINED3D_DECL_METHOD_LOOKUP = 5, WINED3D_DECL_METHOD_LOOKUP_PRESAMPLED = 6 };
enum wined3d_decl_usage { WINED3D_DECL_USAGE_POSITION = 0, WINED3D_DECL_USAGE_BLEND_WEIGHT = 1, WINED3D_DECL_USAGE_BLEND_INDICES = 2, WINED3D_DECL_USAGE_NORMAL = 3, WINED3D_DECL_USAGE_PSIZE = 4, WINED3D_DECL_USAGE_TEXCOORD = 5, WINED3D_DECL_USAGE_TANGENT = 6, WINED3D_DECL_USAGE_BINORMAL = 7, WINED3D_DECL_USAGE_TESS_FACTOR = 8, WINED3D_DECL_USAGE_POSITIONT = 9, WINED3D_DECL_USAGE_COLOR = 10, WINED3D_DECL_USAGE_FOG = 11, WINED3D_DECL_USAGE_DEPTH = 12, WINED3D_DECL_USAGE_SAMPLE = 13 };
enum wined3d_scanline_ordering { WINED3D_SCANLINE_ORDERING_UNKNOWN = 0, WINED3D_SCANLINE_ORDERING_PROGRESSIVE = 1, WINED3D_SCANLINE_ORDERING_INTERLACED = 2 };
enum wined3d_shader_type { WINED3D_SHADER_TYPE_PIXEL = 0, WINED3D_SHADER_TYPE_VERTEX = 1, WINED3D_SHADER_TYPE_GEOMETRY = 2, WINED3D_SHADER_TYPE_HULL = 3, WINED3D_SHADER_TYPE_DOMAIN = 4, WINED3D_SHADER_TYPE_GRAPHICS_COUNT = 5, WINED3D_SHADER_TYPE_COMPUTE = 5, WINED3D_SHADER_TYPE_COUNT = 6, WINED3D_SHADER_TYPE_INVALID = 6 };
enum wined3d_input_classification { WINED3D_INPUT_PER_VERTEX_DATA = 0, WINED3D_INPUT_PER_INSTANCE_DATA = 1 };
enum wined3d_ffp_emit_idx { WINED3D_FFP_EMIT_FLOAT1 = 0, WINED3D_FFP_EMIT_FLOAT2 = 1, WINED3D_FFP_EMIT_FLOAT3 = 2, WINED3D_FFP_EMIT_FLOAT4 = 3, WINED3D_FFP_EMIT_D3DCOLOR = 4, WINED3D_FFP_EMIT_UBYTE4 = 5, WINED3D_FFP_EMIT_SHORT2 = 6, WINED3D_FFP_EMIT_SHORT4 = 7, WINED3D_FFP_EMIT_UBYTE4N = 8, WINED3D_FFP_EMIT_SHORT2N = 9, WINED3D_FFP_EMIT_SHORT4N = 10, WINED3D_FFP_EMIT_USHORT2N = 11, WINED3D_FFP_EMIT_USHORT4N = 12, WINED3D_FFP_EMIT_UDEC3 = 13, WINED3D_FFP_EMIT_DEC3N = 14, WINED3D_FFP_EMIT_FLOAT16_2 = 15, WINED3D_FFP_EMIT_FLOAT16_4 = 16, WINED3D_FFP_EMIT_INVALID = 17, WINED3D_FFP_EMIT_COUNT = 18 };
enum fixup_channel_source { CHANNEL_SOURCE_ZERO = 0, CHANNEL_SOURCE_ONE = 1, CHANNEL_SOURCE_X = 2, CHANNEL_SOURCE_Y = 3, CHANNEL_SOURCE_Z = 4, CHANNEL_SOURCE_W = 5, CHANNEL_SOURCE_COMPLEX0 = 6, CHANNEL_SOURCE_COMPLEX1 = 7 };
enum complex_fixup { COMPLEX_FIXUP_NONE = 0, COMPLEX_FIXUP_YUY2 = 1, COMPLEX_FIXUP_UYVY = 2, COMPLEX_FIXUP_YV12 = 3, COMPLEX_FIXUP_P8 = 4, COMPLEX_FIXUP_NV12 = 5, COMPLEX_FIXUP_YUV = 6 };
enum wined3d_shader_resource_type { WINED3D_SHADER_RESOURCE_NONE = 0, WINED3D_SHADER_RESOURCE_BUFFER = 1, WINED3D_SHADER_RESOURCE_TEXTURE_1D = 2, WINED3D_SHADER_RESOURCE_TEXTURE_2D = 3, WINED3D_SHADER_RESOURCE_TEXTURE_2DMS = 4, WINED3D_SHADER_RESOURCE_TEXTURE_3D = 5, WINED3D_SHADER_RESOURCE_TEXTURE_CUBE = 6, WINED3D_SHADER_RESOURCE_TEXTURE_1DARRAY = 7, WINED3D_SHADER_RESOURCE_TEXTURE_2DARRAY = 8, WINED3D_SHADER_RESOURCE_TEXTURE_2DMSARRAY = 9, WINED3D_SHADER_RESOURCE_TEXTURE_CUBEARRAY = 10 };
enum wined3d_shader_register_type { WINED3DSPR_TEMP = 0, WINED3DSPR_INPUT = 1, WINED3DSPR_CONST = 2, WINED3DSPR_ADDR = 3, WINED3DSPR_TEXTURE = 3, WINED3DSPR_RASTOUT = 4, WINED3DSPR_ATTROUT = 5, WINED3DSPR_TEXCRDOUT = 6, WINED3DSPR_OUTPUT = 6, WINED3DSPR_CONSTINT = 7, WINED3DSPR_COLOROUT = 8, WINED3DSPR_DEPTHOUT = 9, WINED3DSPR_SAMPLER = 10, WINED3DSPR_CONST2 = 11, WINED3DSPR_CONST3 = 12, WINED3DSPR_CONST4 = 13, WINED3DSPR_CONSTBOOL = 14, WINED3DSPR_LOOP = 15, WINED3DSPR_TEMPFLOAT16 = 16, WINED3DSPR_MISCTYPE = 17, WINED3DSPR_LABEL = 18, WINED3DSPR_PREDICATE = 19, WINED3DSPR_IMMCONST = 20, WINED3DSPR_CONSTBUFFER = 21, WINED3DSPR_IMMCONSTBUFFER = 22, WINED3DSPR_PRIMID = 23, WINED3DSPR_NULL = 24, WINED3DSPR_RESOURCE = 25, WINED3DSPR_UAV = 26, WINED3DSPR_OUTPOINTID = 27, WINED3DSPR_FORKINSTID = 28, WINED3DSPR_JOININSTID = 29, WINED3DSPR_INCONTROLPOINT = 30, WINED3DSPR_OUTCONTROLPOINT = 31, WINED3DSPR_PATCHCONST = 32, WINED3DSPR_TESSCOORD = 33, WINED3DSPR_GROUPSHAREDMEM = 34, WINED3DSPR_THREADID = 35, WINED3DSPR_THREADGROUPID = 36, WINED3DSPR_LOCALTHREADID = 37, WINED3DSPR_LOCALTHREADINDEX = 38, WINED3DSPR_IDXTEMP = 39, WINED3DSPR_STREAM = 40, WINED3DSPR_FUNCTIONBODY = 41, WINED3DSPR_FUNCTIONPOINTER = 42, WINED3DSPR_COVERAGE = 43, WINED3DSPR_SAMPLEMASK = 44, WINED3DSPR_GSINSTID = 45, WINED3DSPR_DEPTHOUTGE = 46, WINED3DSPR_DEPTHOUTLE = 47, WINED3DSPR_RASTERIZER = 48, WINED3DSPR_STENCILREF = 49 };
enum wined3d_data_type { WINED3D_DATA_FLOAT = 0, WINED3D_DATA_INT = 1, WINED3D_DATA_RESOURCE = 2, WINED3D_DATA_SAMPLER = 3, WINED3D_DATA_UAV = 4, WINED3D_DATA_UINT = 5, WINED3D_DATA_UNORM = 6, WINED3D_DATA_SNORM = 7, WINED3D_DATA_OPAQUE = 8 };
enum wined3d_immconst_type { WINED3D_IMMCONST_SCALAR = 0, WINED3D_IMMCONST_VEC4 = 1 };
enum wined3d_shader_src_modifier { WINED3DSPSM_NONE = 0, WINED3DSPSM_NEG = 1, WINED3DSPSM_BIAS = 2, WINED3DSPSM_BIASNEG = 3, WINED3DSPSM_SIGN = 4, WINED3DSPSM_SIGNNEG = 5, WINED3DSPSM_COMP = 6, WINED3DSPSM_X2 = 7, WINED3DSPSM_X2NEG = 8, WINED3DSPSM_DZ = 9, WINED3DSPSM_DW = 10, WINED3DSPSM_ABS = 11, WINED3DSPSM_ABSNEG = 12, WINED3DSPSM_NOT = 13 };
enum wined3d_tessellator_domain { WINED3D_TESSELLATOR_DOMAIN_LINE = 1, WINED3D_TESSELLATOR_DOMAIN_TRIANGLE = 2, WINED3D_TESSELLATOR_DOMAIN_QUAD = 3 };
enum wined3d_tessellator_output_primitive { WINED3D_TESSELLATOR_OUTPUT_POINT = 1, WINED3D_TESSELLATOR_OUTPUT_LINE = 2, WINED3D_TESSELLATOR_OUTPUT_TRIANGLE_CW = 3, WINED3D_TESSELLATOR_OUTPUT_TRIANGLE_CCW = 4 };
enum wined3d_tessellator_partitioning { WINED3D_TESSELLATOR_PARTITIONING_INTEGER = 1, WINED3D_TESSELLATOR_PARTITIONING_POW2 = 2, WINED3D_TESSELLATOR_PARTITIONING_FRACTIONAL_ODD = 3, WINED3D_TESSELLATOR_PARTITIONING_FRACTIONAL_EVEN = 4 };
enum wined3d_sysval_semantic { WINED3D_SV_POSITION = 1, WINED3D_SV_CLIP_DISTANCE = 2, WINED3D_SV_CULL_DISTANCE = 3, WINED3D_SV_RENDER_TARGET_ARRAY_INDEX = 4, WINED3D_SV_VIEWPORT_ARRAY_INDEX = 5, WINED3D_SV_VERTEX_ID = 6, WINED3D_SV_PRIMITIVE_ID = 7, WINED3D_SV_INSTANCE_ID = 8, WINED3D_SV_IS_FRONT_FACE = 9, WINED3D_SV_SAMPLE_INDEX = 10, WINED3D_SV_TESS_FACTOR_QUADEDGE = 11, WINED3D_SV_TESS_FACTOR_QUADINT = 12, WINED3D_SV_TESS_FACTOR_TRIEDGE = 13, WINED3D_SV_TESS_FACTOR_TRIINT = 14, WINED3D_SV_TESS_FACTOR_LINEDET = 15, WINED3D_SV_TESS_FACTOR_LINEDEN = 16 };
enum wined3d_component_type { WINED3D_TYPE_UNKNOWN = 0, WINED3D_TYPE_UINT = 1, WINED3D_TYPE_INT = 2, WINED3D_TYPE_FLOAT = 3 };
enum WINED3D_SHADER_INSTRUCTION_HANDLER { WINED3DSIH_ABS = 0, WINED3DSIH_ADD = 1, WINED3DSIH_AND = 2, WINED3DSIH_ATOMIC_AND = 3, WINED3DSIH_ATOMIC_CMP_STORE = 4, WINED3DSIH_ATOMIC_IADD = 5, WINED3DSIH_ATOMIC_IMAX = 6, WINED3DSIH_ATOMIC_IMIN = 7, WINED3DSIH_ATOMIC_OR = 8, WINED3DSIH_ATOMIC_UMAX = 9, WINED3DSIH_ATOMIC_UMIN = 10, WINED3DSIH_ATOMIC_XOR = 11, WINED3DSIH_BEM = 12, WINED3DSIH_BFI = 13, WINED3DSIH_BFREV = 14, WINED3DSIH_BREAK = 15, WINED3DSIH_BREAKC = 16, WINED3DSIH_BREAKP = 17, WINED3DSIH_BUFINFO = 18, WINED3DSIH_CALL = 19, WINED3DSIH_CALLNZ = 20, WINED3DSIH_CASE = 21, WINED3DSIH_CMP = 22, WINED3DSIH_CND = 23, WINED3DSIH_CONTINUE = 24, WINED3DSIH_CONTINUEP = 25, WINED3DSIH_COUNTBITS = 26, WINED3DSIH_CRS = 27, WINED3DSIH_CUT = 28, WINED3DSIH_CUT_STREAM = 29, WINED3DSIH_DCL = 30, WINED3DSIH_DCL_CONSTANT_BUFFER = 31, WINED3DSIH_DCL_FUNCTION_BODY = 32, WINED3DSIH_DCL_FUNCTION_TABLE = 33, WINED3DSIH_DCL_GLOBAL_FLAGS = 34, WINED3DSIH_DCL_GS_INSTANCES = 35, WINED3DSIH_DCL_HS_FORK_PHASE_INSTANCE_COUNT = 36, WINED3DSIH_DCL_HS_JOIN_PHASE_INSTANCE_COUNT = 37, WINED3DSIH_DCL_HS_MAX_TESSFACTOR = 38, WINED3DSIH_DCL_IMMEDIATE_CONSTANT_BUFFER = 39, WINED3DSIH_DCL_INDEX_RANGE = 40, WINED3DSIH_DCL_INDEXABLE_TEMP = 41, WINED3DSIH_DCL_INPUT = 42, WINED3DSIH_DCL_INPUT_CONTROL_POINT_COUNT = 43, WINED3DSIH_DCL_INPUT_PRIMITIVE = 44, WINED3DSIH_DCL_INPUT_PS = 45, WINED3DSIH_DCL_INPUT_PS_SGV = 46, WINED3DSIH_DCL_INPUT_PS_SIV = 47, WINED3DSIH_DCL_INPUT_SGV = 48, WINED3DSIH_DCL_INPUT_SIV = 49, WINED3DSIH_DCL_INTERFACE = 50, WINED3DSIH_DCL_OUTPUT = 51, WINED3DSIH_DCL_OUTPUT_CONTROL_POINT_COUNT = 52, WINED3DSIH_DCL_OUTPUT_SIV = 53, WINED3DSIH_DCL_OUTPUT_TOPOLOGY = 54, WINED3DSIH_DCL_RESOURCE_RAW = 55, WINED3DSIH_DCL_RESOURCE_STRUCTURED = 56, WINED3DSIH_DCL_SAMPLER = 57, WINED3DSIH_DCL_STREAM = 58, WINED3DSIH_DCL_TEMPS = 59, WINED3DSIH_DCL_TESSELLATOR_DOMAIN = 60, WINED3DSIH_DCL_TESSELLATOR_OUTPUT_PRIMITIVE = 61, WINED3DSIH_DCL_TESSELLATOR_PARTITIONING = 62, WINED3DSIH_DCL_TGSM_RAW = 63, WINED3DSIH_DCL_TGSM_STRUCTURED = 64, WINED3DSIH_DCL_THREAD_GROUP = 65, WINED3DSIH_DCL_UAV_RAW = 66, WINED3DSIH_DCL_UAV_STRUCTURED = 67, WINED3DSIH_DCL_UAV_TYPED = 68, WINED3DSIH_DCL_VERTICES_OUT = 69, WINED3DSIH_DEF = 70, WINED3DSIH_DEFAULT = 71, WINED3DSIH_DEFB = 72, WINED3DSIH_DEFI = 73, WINED3DSIH_DIV = 74, WINED3DSIH_DP2 = 75, WINED3DSIH_DP2ADD = 76, WINED3DSIH_DP3 = 77, WINED3DSIH_DP4 = 78, WINED3DSIH_DST = 79, WINED3DSIH_DSX = 80, WINED3DSIH_DSX_COARSE = 81, WINED3DSIH_DSX_FINE = 82, WINED3DSIH_DSY = 83, WINED3DSIH_DSY_COARSE = 84, WINED3DSIH_DSY_FINE = 85, WINED3DSIH_ELSE = 86, WINED3DSIH_EMIT = 87, WINED3DSIH_EMIT_STREAM = 88, WINED3DSIH_ENDIF = 89, WINED3DSIH_ENDLOOP = 90, WINED3DSIH_ENDREP = 91, WINED3DSIH_ENDSWITCH = 92, WINED3DSIH_EQ = 93, WINED3DSIH_EVAL_CENTROID = 94, WINED3DSIH_EVAL_SAMPLE_INDEX = 95, WINED3DSIH_EXP = 96, WINED3DSIH_EXPP = 97, WINED3DSIH_F16TOF32 = 98, WINED3DSIH_F32TOF16 = 99, WINED3DSIH_FCALL = 100, WINED3DSIH_FIRSTBIT_HI = 101, WINED3DSIH_FIRSTBIT_LO = 102, WINED3DSIH_FIRSTBIT_SHI = 103, WINED3DSIH_FRC = 104, WINED3DSIH_FTOI = 105, WINED3DSIH_FTOU = 106, WINED3DSIH_GATHER4 = 107, WINED3DSIH_GATHER4_C = 108, WINED3DSIH_GATHER4_PO = 109, WINED3DSIH_GATHER4_PO_C = 110, WINED3DSIH_GE = 111, WINED3DSIH_HS_CONTROL_POINT_PHASE = 112, WINED3DSIH_HS_DECLS = 113, WINED3DSIH_HS_FORK_PHASE = 114, WINED3DSIH_HS_JOIN_PHASE = 115, WINED3DSIH_IADD = 116, WINED3DSIH_IBFE = 117, WINED3DSIH_IEQ = 118, WINED3DSIH_IF = 119, WINED3DSIH_IFC = 120, WINED3DSIH_IGE = 121, WINED3DSIH_ILT = 122, WINED3DSIH_IMAD = 123, WINED3DSIH_IMAX = 124, WINED3DSIH_IMIN = 125, WINED3DSIH_IMM_ATOMIC_ALLOC = 126, WINED3DSIH_IMM_ATOMIC_AND = 127, WINED3DSIH_IMM_ATOMIC_CMP_EXCH = 128, WINED3DSIH_IMM_ATOMIC_CONSUME = 129, WINED3DSIH_IMM_ATOMIC_EXCH = 130, WINED3DSIH_IMM_ATOMIC_IADD = 131, WINED3DSIH_IMM_ATOMIC_IMAX = 132, WINED3DSIH_IMM_ATOMIC_IMIN = 133, WINED3DSIH_IMM_ATOMIC_OR = 134, WINED3DSIH_IMM_ATOMIC_UMAX = 135, WINED3DSIH_IMM_ATOMIC_UMIN = 136, WINED3DSIH_IMM_ATOMIC_XOR = 137, WINED3DSIH_IMUL = 138, WINED3DSIH_INE = 139, WINED3DSIH_INEG = 140, WINED3DSIH_ISHL = 141, WINED3DSIH_ISHR = 142, WINED3DSIH_ITOF = 143, WINED3DSIH_LABEL = 144, WINED3DSIH_LD = 145, WINED3DSIH_LD2DMS = 146, WINED3DSIH_LD_RAW = 147, WINED3DSIH_LD_STRUCTURED = 148, WINED3DSIH_LD_UAV_TYPED = 149, WINED3DSIH_LIT = 150, WINED3DSIH_LOD = 151, WINED3DSIH_LOG = 152, WINED3DSIH_LOGP = 153, WINED3DSIH_LOOP = 154, WINED3DSIH_LRP = 155, WINED3DSIH_LT = 156, WINED3DSIH_M3x2 = 157, WINED3DSIH_M3x3 = 158, WINED3DSIH_M3x4 = 159, WINED3DSIH_M4x3 = 160, WINED3DSIH_M4x4 = 161, WINED3DSIH_MAD = 162, WINED3DSIH_MAX = 163, WINED3DSIH_MIN = 164, WINED3DSIH_MOV = 165, WINED3DSIH_MOVA = 166, WINED3DSIH_MOVC = 167, WINED3DSIH_MUL = 168, WINED3DSIH_NE = 169, WINED3DSIH_NOP = 170, WINED3DSIH_NOT = 171, WINED3DSIH_NRM = 172, WINED3DSIH_OR = 173, WINED3DSIH_PHASE = 174, WINED3DSIH_POW = 175, WINED3DSIH_RCP = 176, WINED3DSIH_REP = 177, WINED3DSIH_RESINFO = 178, WINED3DSIH_RET = 179, WINED3DSIH_RETP = 180, WINED3DSIH_ROUND_NE = 181, WINED3DSIH_ROUND_NI = 182, WINED3DSIH_ROUND_PI = 183, WINED3DSIH_ROUND_Z = 184, WINED3DSIH_RSQ = 185, WINED3DSIH_SAMPLE = 186, WINED3DSIH_SAMPLE_B = 187, WINED3DSIH_SAMPLE_C = 188, WINED3DSIH_SAMPLE_C_LZ = 189, WINED3DSIH_SAMPLE_GRAD = 190, WINED3DSIH_SAMPLE_INFO = 191, WINED3DSIH_SAMPLE_LOD = 192, WINED3DSIH_SAMPLE_POS = 193, WINED3DSIH_SETP = 194, WINED3DSIH_SGE = 195, WINED3DSIH_SGN = 196, WINED3DSIH_SINCOS = 197, WINED3DSIH_SLT = 198, WINED3DSIH_SQRT = 199, WINED3DSIH_STORE_RAW = 200, WINED3DSIH_STORE_STRUCTURED = 201, WINED3DSIH_STORE_UAV_TYPED = 202, WINED3DSIH_SUB = 203, WINED3DSIH_SWAPC = 204, WINED3DSIH_SWITCH = 205, WINED3DSIH_SYNC = 206, WINED3DSIH_TEX = 207, WINED3DSIH_TEXBEM = 208, WINED3DSIH_TEXBEML = 209, WINED3DSIH_TEXCOORD = 210, WINED3DSIH_TEXDEPTH = 211, WINED3DSIH_TEXDP3 = 212, WINED3DSIH_TEXDP3TEX = 213, WINED3DSIH_TEXKILL = 214, WINED3DSIH_TEXLDD = 215, WINED3DSIH_TEXLDL = 216, WINED3DSIH_TEXM3x2DEPTH = 217, WINED3DSIH_TEXM3x2PAD = 218, WINED3DSIH_TEXM3x2TEX = 219, WINED3DSIH_TEXM3x3 = 220, WINED3DSIH_TEXM3x3DIFF = 221, WINED3DSIH_TEXM3x3PAD = 222, WINED3DSIH_TEXM3x3SPEC = 223, WINED3DSIH_TEXM3x3TEX = 224, WINED3DSIH_TEXM3x3VSPEC = 225, WINED3DSIH_TEXREG2AR = 226, WINED3DSIH_TEXREG2GB = 227, WINED3DSIH_TEXREG2RGB = 228, WINED3DSIH_UBFE = 229, WINED3DSIH_UDIV = 230, WINED3DSIH_UGE = 231, WINED3DSIH_ULT = 232, WINED3DSIH_UMAX = 233, WINED3DSIH_UMIN = 234, WINED3DSIH_UMUL = 235, WINED3DSIH_USHR = 236, WINED3DSIH_UTOF = 237, WINED3DSIH_XOR = 238, WINED3DSIH_TABLE_SIZE = 239 };
enum wined3d_shader_input_sysval_semantic { WINED3D_SIV_POSITION = 1, WINED3D_SIV_CLIP_DISTANCE = 2, WINED3D_SIV_CULL_DISTANCE = 3, WINED3D_SIV_RENDER_TARGET_ARRAY_INDEX = 4, WINED3D_SIV_VIEWPORT_ARRAY_INDEX = 5, WINED3D_SIV_VERTEX_ID = 6, WINED3D_SIV_PRIMITIVE_ID = 7, WINED3D_SIV_INSTANCE_ID = 8, WINED3D_SIV_IS_FRONT_FACE = 9, WINED3D_SIV_SAMPLE_INDEX = 10, WINED3D_SIV_QUAD_U0_TESS_FACTOR = 11, WINED3D_SIV_QUAD_V0_TESS_FACTOR = 12, WINED3D_SIV_QUAD_U1_TESS_FACTOR = 13, WINED3D_SIV_QUAD_V1_TESS_FACTOR = 14, WINED3D_SIV_QUAD_U_INNER_TESS_FACTOR = 15, WINED3D_SIV_QUAD_V_INNER_TESS_FACTOR = 16, WINED3D_SIV_TRIANGLE_U_TESS_FACTOR = 17, WINED3D_SIV_TRIANGLE_V_TESS_FACTOR = 18, WINED3D_SIV_TRIANGLE_W_TESS_FACTOR = 19, WINED3D_SIV_TRIANGLE_INNER_TESS_FACTOR = 20, WINED3D_SIV_LINE_DETAIL_TESS_FACTOR = 21, WINED3D_SIV_LINE_DENSITY_TESS_FACTOR = 22 };
enum wined3d_gl_resource_type { WINED3D_GL_RES_TYPE_TEX_1D = 0, WINED3D_GL_RES_TYPE_TEX_2D = 1, WINED3D_GL_RES_TYPE_TEX_3D = 2, WINED3D_GL_RES_TYPE_TEX_CUBE = 3, WINED3D_GL_RES_TYPE_BUFFER = 4, WINED3D_GL_RES_TYPE_RB = 5, WINED3D_GL_RES_TYPE_COUNT = 6 };
enum wined3d_ffp_ps_fog_mode { WINED3D_FFP_PS_FOG_OFF = 0, WINED3D_FFP_PS_FOG_LINEAR = 1, WINED3D_FFP_PS_FOG_EXP = 2, WINED3D_FFP_PS_FOG_EXP2 = 3 };
enum wined3d_query_state { QUERY_CREATED = 0, QUERY_SIGNALLED = 1, QUERY_BUILDING = 2 };
enum wined3d_blit_op { WINED3D_BLIT_OP_COLOR_BLIT = 0, WINED3D_BLIT_OP_COLOR_BLIT_ALPHATEST = 1, WINED3D_BLIT_OP_COLOR_BLIT_CKEY = 2, WINED3D_BLIT_OP_DEPTH_BLIT = 3, WINED3D_BLIT_OP_RAW_BLIT = 4 };
enum wined3d_pci_vendor { HW_VENDOR_SOFTWARE = 0, HW_VENDOR_AMD = 4098, HW_VENDOR_NVIDIA = 4318, HW_VENDOR_VMWARE = 5549, HW_VENDOR_REDHAT = 6900, HW_VENDOR_INTEL = 32902 };
enum wined3d_pci_device { CARD_WINE = 0, CARD_AMD_RAGE_128PRO = 21062, CARD_AMD_RADEON_7200 = 20804, CARD_AMD_RADEON_8500 = 20812, CARD_AMD_RADEON_9500 = 16708, CARD_AMD_RADEON_XPRESS_200M = 22869, CARD_AMD_RADEON_X700 = 24140, CARD_AMD_RADEON_X1600 = 29122, CARD_AMD_RADEON_HD2350 = 38087, CARD_AMD_RADEON_HD2600 = 38273, CARD_AMD_RADEON_HD2900 = 37888, CARD_AMD_RADEON_HD3200 = 38432, CARD_AMD_RADEON_HD3850 = 38165, CARD_AMD_RADEON_HD4200M = 38674, CARD_AMD_RADEON_HD4350 = 38223, CARD_AMD_RADEON_HD4600 = 38037, CARD_AMD_RADEON_HD4700 = 37966, CARD_AMD_RADEON_HD4800 = 37964, CARD_AMD_RADEON_HD5400 = 26873, CARD_AMD_RADEON_HD5600 = 26840, CARD_AMD_RADEON_HD5700 = 26814, CARD_AMD_RADEON_HD5800 = 26776, CARD_AMD_RADEON_HD5900 = 26780, CARD_AMD_RADEON_HD6300 = 38915, CARD_AMD_RADEON_HD6400 = 26480, CARD_AMD_RADEON_HD6490M = 26464, CARD_AMD_RADEON_HD6410D = 38468, CARD_AMD_RADEON_HD6480G = 38472, CARD_AMD_RADEON_HD6550D = 38464, CARD_AMD_RADEON_HD6600 = 26456, CARD_AMD_RADEON_HD6600M = 26433, CARD_AMD_RADEON_HD6700 = 26810, CARD_AMD_RADEON_HD6800 = 26425, CARD_AMD_RADEON_HD6900 = 26393, CARD_AMD_RADEON_HD7660D = 39169, CARD_AMD_RADEON_HD7700 = 26685, CARD_AMD_RADEON_HD7800 = 26649, CARD_AMD_RADEON_HD7870 = 26648, CARD_AMD_RADEON_HD7900 = 26522, CARD_AMD_RADEON_HD8600M = 26208, CARD_AMD_RADEON_HD8670 = 26128, CARD_AMD_RADEON_HD8770 = 26204, CARD_AMD_RADEON_R3 = 38960, CARD_AMD_RADEON_R7 = 4879, CARD_AMD_RADEON_R9_285 = 26937, CARD_AMD_RADEON_R9_290 = 26545, CARD_AMD_RADEON_R9_290X = 26544, CARD_AMD_RADEON_R9_FURY = 29440, CARD_AMD_RADEON_R9_M370X = 26657, CARD_AMD_RADEON_R9_M380 = 26183, CARD_AMD_RADEON_R9_M395X = 26912, CARD_AMD_RADEON_RX_460 = 26607, CARD_AMD_RADEON_RX_480 = 26591, CARD_AMD_RADEON_RX_VEGA_10 = 26751, CARD_AMD_RADEON_RX_VEGA_12 = 27055, CARD_AMD_RADEON_RAVEN = 5597, CARD_AMD_RADEON_RX_VEGA_20 = 26287, CARD_AMD_RADEON_RX_NAVI_10 = 29471, CARD_AMD_RADEON_RX_NAVI_14 = 29504, CARD_AMD_RADEON_RX_NAVI_21 = 29631, CARD_AMD_RADEON_RX_NAVI_44 = 30096, CARD_AMD_RADEON_PRO_V620 = 29601, CARD_AMD_RADEON_PRO_V620_VF = 29614, CARD_AMD_RADEON_RX_6700_XT = 29663, CARD_AMD_VANGOGH = 5695, CARD_AMD_RAPHAEL = 5710, CARD_NVIDIA_RIVA_128 = 24, CARD_NVIDIA_RIVA_TNT = 32, CARD_NVIDIA_RIVA_TNT2 = 40, CARD_NVIDIA_GEFORCE = 256, CARD_NVIDIA_GEFORCE2_MX = 272, CARD_NVIDIA_GEFORCE2 = 336, CARD_NVIDIA_GEFORCE3 = 512, CARD_NVIDIA_GEFORCE4_MX = 368, CARD_NVIDIA_GEFORCE4_TI4200 = 595, CARD_NVIDIA_GEFORCEFX_5200 = 800, CARD_NVIDIA_GEFORCEFX_5600 = 786, CARD_NVIDIA_GEFORCEFX_5800 = 770, CARD_NVIDIA_GEFORCE_6200 = 335, CARD_NVIDIA_GEFORCE_6600GT = 320, CARD_NVIDIA_GEFORCE_6800 = 65, CARD_NVIDIA_GEFORCE_7300 = 471, CARD_NVIDIA_GEFORCE_7400 = 472, CARD_NVIDIA_GEFORCE_7600 = 913, CARD_NVIDIA_GEFORCE_7800GT = 146, CARD_NVIDIA_GEFORCE_8200 = 2121, CARD_NVIDIA_GEFORCE_8300GS = 1059, CARD_NVIDIA_GEFORCE_8400GS = 1028, CARD_NVIDIA_GEFORCE_8500GT = 1057, CARD_NVIDIA_GEFORCE_8600GT = 1026, CARD_NVIDIA_GEFORCE_8600MGT = 1031, CARD_NVIDIA_GEFORCE_8800GTS = 403, CARD_NVIDIA_GEFORCE_8800GTX = 401, CARD_NVIDIA_GEFORCE_9200 = 2157, CARD_NVIDIA_GEFORCE_9300 = 2156, CARD_NVIDIA_GEFORCE_9400M = 2147, CARD_NVIDIA_GEFORCE_9400GT = 1068, CARD_NVIDIA_GEFORCE_9500GT = 1600, CARD_NVIDIA_GEFORCE_9600GT = 1570, CARD_NVIDIA_GEFORCE_9700MGT = 1610, CARD_NVIDIA_GEFORCE_9800GT = 1556, CARD_NVIDIA_GEFORCE_210 = 2595, CARD_NVIDIA_GEFORCE_GT220 = 2592, CARD_NVIDIA_GEFORCE_GT240 = 3235, CARD_NVIDIA_GEFORCE_GTS250 = 1557, CARD_NVIDIA_GEFORCE_GTX260 = 1506, CARD_NVIDIA_GEFORCE_GTX275 = 1510, CARD_NVIDIA_GEFORCE_GTX280 = 1505, CARD_NVIDIA_GEFORCE_315M = 2682, CARD_NVIDIA_GEFORCE_320M = 2211, CARD_NVIDIA_GEFORCE_GT320M = 2605, CARD_NVIDIA_GEFORCE_GT325M = 2613, CARD_NVIDIA_GEFORCE_GT330 = 3232, CARD_NVIDIA_GEFORCE_GTS350M = 3248, CARD_NVIDIA_GEFORCE_410M = 4181, CARD_NVIDIA_GEFORCE_GT420 = 3554, CARD_NVIDIA_GEFORCE_GT425M = 3568, CARD_NVIDIA_GEFORCE_GT430 = 3553, CARD_NVIDIA_GEFORCE_GT440 = 3552, CARD_NVIDIA_GEFORCE_GTS450 = 3524, CARD_NVIDIA_GEFORCE_GTX460 = 3618, CARD_NVIDIA_GEFORCE_GTX460M = 3537, CARD_NVIDIA_GEFORCE_GTX465 = 1732, CARD_NVIDIA_GEFORCE_GTX470 = 1741, CARD_NVIDIA_GEFORCE_GTX480 = 1728, CARD_NVIDIA_GEFORCE_GT520 = 4160, CARD_NVIDIA_GEFORCE_GT525M = 3564, CARD_NVIDIA_GEFORCE_GT540M = 3572, CARD_NVIDIA_GEFORCE_GTX550 = 4676, CARD_NVIDIA_GEFORCE_GT555M = 1208, CARD_NVIDIA_GEFORCE_GTX560TI = 4608, CARD_NVIDIA_GEFORCE_GTX560M = 4689, CARD_NVIDIA_GEFORCE_GTX560 = 4609, CARD_NVIDIA_GEFORCE_GTX570 = 4225, CARD_NVIDIA_GEFORCE_GTX580 = 4224, CARD_NVIDIA_GEFORCE_GT610 = 4170, CARD_NVIDIA_GEFORCE_GT630 = 3840, CARD_NVIDIA_GEFORCE_GT630M = 3561, CARD_NVIDIA_GEFORCE_GT640 = 4033, CARD_NVIDIA_GEFORCE_GT640M = 4050, CARD_NVIDIA_GEFORCE_GT650M = 4049, CARD_NVIDIA_GEFORCE_GTX650 = 4038, CARD_NVIDIA_GEFORCE_GTX650TI = 4550, CARD_NVIDIA_GEFORCE_GTX660 = 4544, CARD_NVIDIA_GEFORCE_GTX660M = 4052, CARD_NVIDIA_GEFORCE_GTX660TI = 4483, CARD_NVIDIA_GEFORCE_GTX670 = 4489, CARD_NVIDIA_GEFORCE_GTX670MX = 4513, CARD_NVIDIA_GEFORCE_GTX675MX_1 = 4519, CARD_NVIDIA_GEFORCE_GTX675MX_2 = 4514, CARD_NVIDIA_GEFORCE_GTX680 = 4480, CARD_NVIDIA_GEFORCE_GTX690 = 4488, CARD_NVIDIA_GEFORCE_GT720 = 4747, CARD_NVIDIA_GEFORCE_GT730 = 4743, CARD_NVIDIA_GEFORCE_GT730M = 4065, CARD_NVIDIA_GEFORCE_GT740M = 4754, CARD_NVIDIA_GEFORCE_GT750M = 4073, CARD_NVIDIA_GEFORCE_GT755M = 4045, CARD_NVIDIA_GEFORCE_GTX750 = 4993, CARD_NVIDIA_GEFORCE_GTX750TI = 4992, CARD_NVIDIA_GEFORCE_GTX760 = 4487, CARD_NVIDIA_GEFORCE_GTX760TI = 4499, CARD_NVIDIA_GEFORCE_GTX765M = 4578, CARD_NVIDIA_GEFORCE_GTX770M = 4576, CARD_NVIDIA_GEFORCE_GTX770 = 4484, CARD_NVIDIA_GEFORCE_GTX775M = 4509, CARD_NVIDIA_GEFORCE_GTX780 = 4100, CARD_NVIDIA_GEFORCE_GTX780M = 4510, CARD_NVIDIA_GEFORCE_GTX780TI = 4106, CARD_NVIDIA_GEFORCE_GTXTITAN = 4101, CARD_NVIDIA_GEFORCE_GTXTITANB = 4108, CARD_NVIDIA_GEFORCE_GTXTITANX = 6082, CARD_NVIDIA_GEFORCE_GTXTITANZ = 4097, CARD_NVIDIA_GEFORCE_820M = 4077, CARD_NVIDIA_GEFORCE_830M = 4928, CARD_NVIDIA_GEFORCE_840M = 4929, CARD_NVIDIA_GEFORCE_845M = 4932, CARD_NVIDIA_GEFORCE_GTX850M = 5009, CARD_NVIDIA_GEFORCE_GTX860M = 5010, CARD_NVIDIA_GEFORCE_GTX870M = 4505, CARD_NVIDIA_GEFORCE_GTX880M = 4504, CARD_NVIDIA_GEFORCE_940M = 4935, CARD_NVIDIA_GEFORCE_GTX950 = 5122, CARD_NVIDIA_GEFORCE_GTX950M = 5018, CARD_NVIDIA_GEFORCE_GTX960 = 5121, CARD_NVIDIA_GEFORCE_GTX960M = 5019, CARD_NVIDIA_GEFORCE_GTX970 = 5058, CARD_NVIDIA_GEFORCE_GTX970M = 5080, CARD_NVIDIA_GEFORCE_GTX980 = 5056, CARD_NVIDIA_GEFORCE_GTX980TI = 6088, CARD_NVIDIA_GEFORCE_GT1030 = 7425, CARD_NVIDIA_GEFORCE_GTX1050 = 7297, CARD_NVIDIA_GEFORCE_GTX1050TI = 7298, CARD_NVIDIA_GEFORCE_GTX1060_3GB = 7170, CARD_NVIDIA_GEFORCE_GTX1060 = 7171, CARD_NVIDIA_GEFORCE_GTX1060M = 7200, CARD_NVIDIA_GEFORCE_GTX1070 = 7041, CARD_NVIDIA_GEFORCE_GTX1070M = 7137, CARD_NVIDIA_GEFORCE_GTX1080 = 7040, CARD_NVIDIA_GEFORCE_GTX1080M = 7136, CARD_NVIDIA_GEFORCE_GTX1080TI = 6918, CARD_NVIDIA_TITANX_PASCAL = 6912, CARD_NVIDIA_TITANV = 7553, CARD_NVIDIA_GEFORCE_GTX1650 = 8066, CARD_NVIDIA_GEFORCE_GTX1650SUPER = 8583, CARD_NVIDIA_GEFORCE_GTX1660SUPER = 8644, CARD_NVIDIA_GEFORCE_GTX1660TI = 8578, CARD_NVIDIA_GEFORCE_RTX2060 = 7944, CARD_NVIDIA_GEFORCE_RTX2070 = 7943, CARD_NVIDIA_GEFORCE_RTX2080 = 7815, CARD_NVIDIA_GEFORCE_RTX2080TI = 7687, CARD_NVIDIA_GEFORCE_RTX3050 = 9479, CARD_NVIDIA_GEFORCE_RTX3060 = 9540, CARD_NVIDIA_GEFORCE_RTX3060_LHR = 9476, CARD_NVIDIA_GEFORCE_RTX3060TI_GA103 = 9236, CARD_NVIDIA_GEFORCE_RTX3060TI_GA104 = 9350, CARD_NVIDIA_GEFORCE_RTX3060TI_GA104_LHR = 9353, CARD_NVIDIA_GEFORCE_RTX3070 = 9348, CARD_NVIDIA_GEFORCE_RTX3070_LHR = 9352, CARD_NVIDIA_GEFORCE_RTX3070_MOBILE = 9373, CARD_NVIDIA_GEFORCE_RTX3070TI = 9346, CARD_NVIDIA_GEFORCE_RTX3080_10GB = 8710, CARD_NVIDIA_GEFORCE_RTX3080_10GB_LHR = 8726, CARD_NVIDIA_GEFORCE_RTX3080_12GB = 8714, CARD_NVIDIA_GEFORCE_RTX3080TI = 8712, CARD_NVIDIA_GEFORCE_RTX3090 = 8708, CARD_NVIDIA_GEFORCE_RTX3090TI = 8707, CARD_NVIDIA_TESLA_T4 = 7864, CARD_NVIDIA_AMPERE_A10 = 8758, CARD_NVIDIA_GEFORCE_RTX4060 = 10370, CARD_NVIDIA_GEFORCE_RTX4060M = 10400, CARD_NVIDIA_GEFORCE_RTX4060TI8G = 10243, CARD_NVIDIA_GEFORCE_RTX4060TI16G = 10245, CARD_NVIDIA_GEFORCE_RTX4070 = 10118, CARD_NVIDIA_GEFORCE_RTX4070SUPER = 10115, CARD_NVIDIA_GEFORCE_RTX4070TI = 10114, CARD_NVIDIA_GEFORCE_RTX4070TISUPER = 9989, CARD_NVIDIA_GEFORCE_RTX4080 = 9988, CARD_NVIDIA_GEFORCE_RTX4080SUPER = 9986, CARD_NVIDIA_GEFORCE_RTX4090 = 9860, CARD_REDHAT_VIRGL = 4112, CARD_VMWARE_SVGA3D = 1029, CARD_INTEL_830M = 13687, CARD_INTEL_855GM = 13698, CARD_INTEL_845G = 9570, CARD_INTEL_865G = 9586, CARD_INTEL_915G = 9602, CARD_INTEL_E7221G = 9610, CARD_INTEL_915GM = 9618, CARD_INTEL_945G = 10098, CARD_INTEL_945GM = 10146, CARD_INTEL_945GME = 10158, CARD_INTEL_Q35 = 10674, CARD_INTEL_G33 = 10690, CARD_INTEL_Q33 = 10706, CARD_INTEL_PNVG = 40961, CARD_INTEL_PNVM = 40977, CARD_INTEL_965Q = 10642, CARD_INTEL_965G = 10626, CARD_INTEL_946GZ = 10610, CARD_INTEL_965GM = 10754, CARD_INTEL_965GME = 10770, CARD_INTEL_GM45 = 10818, CARD_INTEL_IGD = 11778, CARD_INTEL_Q45 = 11794, CARD_INTEL_G45 = 11810, CARD_INTEL_G41 = 11826, CARD_INTEL_B43 = 11922, CARD_INTEL_ILKD = 66, CARD_INTEL_ILKM = 70, CARD_INTEL_SNBD = 290, CARD_INTEL_SNBM = 294, CARD_INTEL_SNBS = 266, CARD_INTEL_IVBD = 354, CARD_INTEL_IVBM = 358, CARD_INTEL_IVBS = 346, CARD_INTEL_HWD = 1042, CARD_INTEL_HWM = 1046, CARD_INTEL_HD5000_1 = 2598, CARD_INTEL_HD5000_2 = 1058, CARD_INTEL_I5100_1 = 2594, CARD_INTEL_I5100_2 = 2602, CARD_INTEL_I5100_3 = 2603, CARD_INTEL_I5100_4 = 2606, CARD_INTEL_IP5200_1 = 3362, CARD_INTEL_IP5200_2 = 3366, CARD_INTEL_IP5200_3 = 3370, CARD_INTEL_IP5200_4 = 3371, CARD_INTEL_IP5200_5 = 3374, CARD_INTEL_IP5200_6 = 3106, CARD_INTEL_HD5300 = 5662, CARD_INTEL_HD5500 = 5654, CARD_INTEL_HD5600 = 5650, CARD_INTEL_HD6000 = 5670, CARD_INTEL_I6100 = 5675, CARD_INTEL_IP6200 = 5666, CARD_INTEL_IPP6300 = 5674, CARD_INTEL_HD510_1 = 6402, CARD_INTEL_HD510_2 = 6406, CARD_INTEL_HD510_3 = 6411, CARD_INTEL_HD515 = 6430, CARD_INTEL_HD520_1 = 6422, CARD_INTEL_HD520_2 = 6433, CARD_INTEL_HD530_1 = 6418, CARD_INTEL_HD530_2 = 6427, CARD_INTEL_HDP530 = 6429, CARD_INTEL_I540 = 6438, CARD_INTEL_I550 = 6439, CARD_INTEL_I555 = 6443, CARD_INTEL_IP555 = 6445, CARD_INTEL_IP580_1 = 6450, CARD_INTEL_IP580_2 = 6459, CARD_INTEL_IPP580_1 = 6458, CARD_INTEL_IPP580_2 = 6461, CARD_INTEL_UHD617 = 34752, CARD_INTEL_UHD620 = 16032, CARD_INTEL_HD615 = 22814, CARD_INTEL_HD620 = 22806, CARD_INTEL_HD630_1 = 22802, CARD_INTEL_HD630_2 = 22811, CARD_INTEL_UHD630_1 = 16027, CARD_INTEL_UHD630_2 = 16017 };
enum wined3d_display_driver { DRIVER_AMD_RAGE_128PRO = 0, DRIVER_AMD_R100 = 1, DRIVER_AMD_R300 = 2, DRIVER_AMD_R600 = 3, DRIVER_AMD_RX = 4, DRIVER_INTEL_GMA800 = 5, DRIVER_INTEL_GMA900 = 6, DRIVER_INTEL_GMA950 = 7, DRIVER_INTEL_GMA3000 = 8, DRIVER_INTEL_HD4000 = 9, DRIVER_NVIDIA_TNT = 10, DRIVER_NVIDIA_GEFORCE2MX = 11, DRIVER_NVIDIA_GEFORCEFX = 12, DRIVER_NVIDIA_GEFORCE6 = 13, DRIVER_NVIDIA_GEFORCE8 = 14, DRIVER_NVIDIA_FERMI = 15, DRIVER_NVIDIA_KEPLER = 16, DRIVER_REDHAT_VIRGL = 17, DRIVER_VMWARE = 18, DRIVER_WINE = 19, DRIVER_UNKNOWN = 20 };
enum wined3d_ffp_vs_fog_mode { WINED3D_FFP_VS_FOG_OFF = 0, WINED3D_FFP_VS_FOG_FOGCOORD = 1, WINED3D_FFP_VS_FOG_DEPTH = 2, WINED3D_FFP_VS_FOG_RANGE = 3 };
enum wined3d_cs_queue_id { WINED3D_CS_QUEUE_DEFAULT = 0, WINED3D_CS_QUEUE_MAP = 1, WINED3D_CS_QUEUE_COUNT = 2 };
enum wined3d_channel_type { WINED3D_CHANNEL_TYPE_NONE = 0, WINED3D_CHANNEL_TYPE_UNORM = 1, WINED3D_CHANNEL_TYPE_SNORM = 2, WINED3D_CHANNEL_TYPE_UINT = 3, WINED3D_CHANNEL_TYPE_SINT = 4, WINED3D_CHANNEL_TYPE_FLOAT = 5, WINED3D_CHANNEL_TYPE_DEPTH = 6, WINED3D_CHANNEL_TYPE_STENCIL = 7, WINED3D_CHANNEL_TYPE_UNUSED = 8 };
enum wined3d_gl_extension { WINED3D_GL_EXT_NONE = 0, APPLE_FENCE = 1, APPLE_FLOAT_PIXELS = 2, APPLE_FLUSH_BUFFER_RANGE = 3, APPLE_FLUSH_RENDER = 4, APPLE_RGB_422 = 5, APPLE_YCBCR_422 = 6, ARB_BASE_INSTANCE = 7, ARB_BLEND_FUNC_EXTENDED = 8, ARB_BUFFER_STORAGE = 9, ARB_CLEAR_BUFFER_OBJECT = 10, ARB_CLEAR_TEXTURE = 11, ARB_CLIP_CONTROL = 12, ARB_COLOR_BUFFER_FLOAT = 13, ARB_COMPUTE_SHADER = 14, ARB_CONSERVATIVE_DEPTH = 15, ARB_COPY_BUFFER = 16, ARB_COPY_IMAGE = 17, ARB_CULL_DISTANCE = 18, ARB_DEBUG_OUTPUT = 19, ARB_DEPTH_BUFFER_FLOAT = 20, ARB_DEPTH_CLAMP = 21, ARB_DEPTH_TEXTURE = 22, ARB_DERIVATIVE_CONTROL = 23, ARB_DRAW_BUFFERS = 24, ARB_DRAW_BUFFERS_BLEND = 25, ARB_DRAW_ELEMENTS_BASE_VERTEX = 26, ARB_DRAW_INDIRECT = 27, ARB_DRAW_INSTANCED = 28, ARB_ES2_COMPATIBILITY = 29, ARB_ES3_COMPATIBILITY = 30, ARB_EXPLICIT_ATTRIB_LOCATION = 31, ARB_FRAGMENT_COORD_CONVENTIONS = 32, ARB_FRAGMENT_LAYER_VIEWPORT = 33, ARB_FRAGMENT_PROGRAM = 34, ARB_FRAGMENT_PROGRAM_SHADOW = 35, ARB_FRAGMENT_SHADER = 36, ARB_FRAMEBUFFER_NO_ATTACHMENTS = 37, ARB_FRAMEBUFFER_OBJECT = 38, ARB_FRAMEBUFFER_SRGB = 39, ARB_GEOMETRY_SHADER4 = 40, ARB_GPU_SHADER5 = 41, ARB_HALF_FLOAT_PIXEL = 42, ARB_HALF_FLOAT_VERTEX = 43, ARB_INSTANCED_ARRAYS = 44, ARB_INTERNALFORMAT_QUERY = 45, ARB_INTERNALFORMAT_QUERY2 = 46, ARB_MAP_BUFFER_ALIGNMENT = 47, ARB_MAP_BUFFER_RANGE = 48, ARB_MULTISAMPLE = 49, ARB_MULTITEXTURE = 50, ARB_OCCLUSION_QUERY = 51, ARB_PIPELINE_STATISTICS_QUERY = 52, ARB_PIXEL_BUFFER_OBJECT = 53, ARB_POINT_PARAMETERS = 54, ARB_POINT_SPRITE = 55, ARB_POLYGON_OFFSET_CLAMP = 56, ARB_PROVOKING_VERTEX = 57, ARB_QUERY_BUFFER_OBJECT = 58, ARB_SAMPLE_SHADING = 59, ARB_SAMPLER_OBJECTS = 60, ARB_SEAMLESS_CUBE_MAP = 61, ARB_SHADER_ATOMIC_COUNTERS = 62, ARB_SHADER_VIEWPORT_LAYER_ARRAY = 63, ARB_SHADER_BIT_ENCODING = 64, ARB_SHADER_IMAGE_LOAD_STORE = 65, ARB_SHADER_IMAGE_SIZE = 66, ARB_SHADER_STENCIL_EXPORT = 67, ARB_SHADER_STORAGE_BUFFER_OBJECT = 68, ARB_SHADER_TEXTURE_IMAGE_SAMPLES = 69, ARB_SHADER_TEXTURE_LOD = 70, ARB_SHADING_LANGUAGE_100 = 71, ARB_SHADING_LANGUAGE_420PACK = 72, ARB_SHADING_LANGUAGE_PACKING = 73, ARB_SHADOW = 74, ARB_STENCIL_TEXTURING = 75, ARB_SYNC = 76, ARB_TESSELLATION_SHADER = 77, ARB_TEXTURE_BORDER_CLAMP = 78, ARB_TEXTURE_BUFFER_OBJECT = 79, ARB_TEXTURE_BUFFER_RANGE = 80, ARB_TEXTURE_COMPRESSION = 81, ARB_TEXTURE_COMPRESSION_BPTC = 82, ARB_TEXTURE_COMPRESSION_RGTC = 83, ARB_TEXTURE_CUBE_MAP = 84, ARB_TEXTURE_CUBE_MAP_ARRAY = 85, ARB_TEXTURE_ENV_COMBINE = 86, ARB_TEXTURE_ENV_DOT3 = 87, ARB_TEXTURE_FILTER_ANISOTROPIC = 88, ARB_TEXTURE_FILTER_MINMAX = 89, ARB_TEXTURE_FLOAT = 90, ARB_TEXTURE_GATHER = 91, ARB_TEXTURE_MIRRORED_REPEAT = 92, ARB_TEXTURE_MIRROR_CLAMP_TO_EDGE = 93, ARB_TEXTURE_MULTISAMPLE = 94, ARB_TEXTURE_NON_POWER_OF_TWO = 95, ARB_TEXTURE_QUERY_LEVELS = 96, ARB_TEXTURE_RG = 97, ARB_TEXTURE_RGB10_A2UI = 98, ARB_TEXTURE_STORAGE = 99, ARB_TEXTURE_STORAGE_MULTISAMPLE = 100, ARB_TEXTURE_SWIZZLE = 101, ARB_TEXTURE_VIEW = 102, ARB_TIMER_QUERY = 103, ARB_TRANSFORM_FEEDBACK2 = 104, ARB_TRANSFORM_FEEDBACK3 = 105, ARB_UNIFORM_BUFFER_OBJECT = 106, ARB_VERTEX_ARRAY_BGRA = 107, ARB_VERTEX_BUFFER_OBJECT = 108, ARB_VERTEX_PROGRAM = 109, ARB_VERTEX_SHADER = 110, ARB_VERTEX_TYPE_10F_11F_11F_REV = 111, ARB_VERTEX_TYPE_2_10_10_10_REV = 112, ARB_VIEWPORT_ARRAY = 113, ARB_TEXTURE_BARRIER = 114, ATI_FRAGMENT_SHADER = 115, ATI_SEPARATE_STENCIL = 116, ATI_TEXTURE_COMPRESSION_3DC = 117, ATI_TEXTURE_ENV_COMBINE3 = 118, ATI_TEXTURE_MIRROR_ONCE = 119, EXT_BLEND_COLOR = 120, EXT_BLEND_EQUATION_SEPARATE = 121, EXT_BLEND_FUNC_SEPARATE = 122, EXT_BLEND_MINMAX = 123, EXT_BLEND_SUBTRACT = 124, EXT_DEPTH_BOUNDS_TEST = 125, EXT_DRAW_BUFFERS2 = 126, EXT_FOG_COORD = 127, EXT_FRAMEBUFFER_BLIT = 128, EXT_FRAMEBUFFER_MULTISAMPLE = 129, EXT_FRAMEBUFFER_MULTISAMPLE_BLIT_SCALED = 130, EXT_FRAMEBUFFER_OBJECT = 131, EXT_GPU_PROGRAM_PARAMETERS = 132, EXT_GPU_SHADER4 = 133, EXT_MEMORY_OBJECT = 134, EXT_PACKED_DEPTH_STENCIL = 135, EXT_PACKED_FLOAT = 136, EXT_POINT_PARAMETERS = 137, EXT_PROVOKING_VERTEX = 138, EXT_SECONDARY_COLOR = 139, EXT_SHADER_INTEGER_MIX = 140, EXT_STENCIL_TWO_SIDE = 141, EXT_STENCIL_WRAP = 142, EXT_TEXTURE3D = 143, EXT_TEXTURE_ARRAY = 144, EXT_TEXTURE_COMPRESSION_RGTC = 145, EXT_TEXTURE_COMPRESSION_S3TC = 146, EXT_TEXTURE_ENV_COMBINE = 147, EXT_TEXTURE_ENV_DOT3 = 148, EXT_TEXTURE_INTEGER = 149, EXT_TEXTURE_LOD_BIAS = 150, EXT_TEXTURE_MIRROR_CLAMP = 151, EXT_TEXTURE_SHADOW_LOD = 152, EXT_TEXTURE_SHARED_EXPONENT = 153, EXT_TEXTURE_SNORM = 154, EXT_TEXTURE_SRGB = 155, EXT_TEXTURE_SRGB_DECODE = 156, NV_FENCE = 157, NV_FOG_DISTANCE = 158, NV_FRAGMENT_PROGRAM = 159, NV_FRAGMENT_PROGRAM2 = 160, NV_FRAGMENT_PROGRAM_OPTION = 161, NV_HALF_FLOAT = 162, NV_LIGHT_MAX_EXPONENT = 163, NV_POINT_SPRITE = 164, NV_REGISTER_COMBINERS = 165, NV_REGISTER_COMBINERS2 = 166, NV_TEXGEN_REFLECTION = 167, NV_TEXTURE_ENV_COMBINE4 = 168, NV_TEXTURE_SHADER = 169, NV_TEXTURE_SHADER2 = 170, NV_VERTEX_PROGRAM = 171, NV_VERTEX_PROGRAM1_1 = 172, NV_VERTEX_PROGRAM2 = 173, NV_VERTEX_PROGRAM2_OPTION = 174, NV_VERTEX_PROGRAM3 = 175, NV_TEXTURE_BARRIER = 176, WGL_ARB_PIXEL_FORMAT = 177, WGL_EXT_SWAP_CONTROL = 178, WGL_WINE_PIXEL_FORMAT_PASSTHROUGH = 179, WGL_WINE_QUERY_RENDERER = 180, WINED3D_GL_BLEND_EQUATION = 181, WINED3D_GL_LEGACY_CONTEXT = 182, WINED3D_GL_NORMALIZED_TEXRECT = 183, WINED3D_GL_PRIMITIVE_QUERY = 184, WINED3D_GL_VERSION_2_0 = 185, WINED3D_GL_VERSION_3_2 = 186, WINED3D_GLSL_130 = 187, WINED3D_GL_EXT_COUNT = 188 };
enum VkAttachmentLoadOp { VK_ATTACHMENT_LOAD_OP_LOAD = 0, VK_ATTACHMENT_LOAD_OP_CLEAR = 1, VK_ATTACHMENT_LOAD_OP_DONT_CARE = 2, VK_ATTACHMENT_LOAD_OP_NONE = 0, VK_ATTACHMENT_LOAD_OP_MAX_ENUM = 0, VK_ATTACHMENT_LOAD_OP_NONE_EXT = 0, VK_ATTACHMENT_LOAD_OP_NONE_KHR = 0 };
enum VkAttachmentStoreOp { VK_ATTACHMENT_STORE_OP_STORE = 0, VK_ATTACHMENT_STORE_OP_DONT_CARE = 1, VK_ATTACHMENT_STORE_OP_NONE = 0, VK_ATTACHMENT_STORE_OP_MAX_ENUM = 0, VK_ATTACHMENT_STORE_OP_NONE_KHR = 0, VK_ATTACHMENT_STORE_OP_NONE_QCOM = 0, VK_ATTACHMENT_STORE_OP_NONE_EXT = 0 };
enum VkBlendFactor { VK_BLEND_FACTOR_ZERO = 0, VK_BLEND_FACTOR_ONE = 1, VK_BLEND_FACTOR_SRC_COLOR = 2, VK_BLEND_FACTOR_ONE_MINUS_SRC_COLOR = 3, VK_BLEND_FACTOR_DST_COLOR = 4, VK_BLEND_FACTOR_ONE_MINUS_DST_COLOR = 5, VK_BLEND_FACTOR_SRC_ALPHA = 6, VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA = 7, VK_BLEND_FACTOR_DST_ALPHA = 8, VK_BLEND_FACTOR_ONE_MINUS_DST_ALPHA = 9, VK_BLEND_FACTOR_CONSTANT_COLOR = 10, VK_BLEND_FACTOR_ONE_MINUS_CONSTANT_COLOR = 11, VK_BLEND_FACTOR_CONSTANT_ALPHA = 12, VK_BLEND_FACTOR_ONE_MINUS_CONSTANT_ALPHA = 13, VK_BLEND_FACTOR_SRC_ALPHA_SATURATE = 14, VK_BLEND_FACTOR_SRC1_COLOR = 15, VK_BLEND_FACTOR_ONE_MINUS_SRC1_COLOR = 16, VK_BLEND_FACTOR_SRC1_ALPHA = 17, VK_BLEND_FACTOR_ONE_MINUS_SRC1_ALPHA = 18, VK_BLEND_FACTOR_MAX_ENUM = 0 };
enum VkBlendOp { VK_BLEND_OP_ADD = 0, VK_BLEND_OP_SUBTRACT = 1, VK_BLEND_OP_REVERSE_SUBTRACT = 2, VK_BLEND_OP_MIN = 3, VK_BLEND_OP_MAX = 4, VK_BLEND_OP_ZERO_EXT = 0, VK_BLEND_OP_SRC_EXT = 0, VK_BLEND_OP_DST_EXT = 0, VK_BLEND_OP_SRC_OVER_EXT = 0, VK_BLEND_OP_DST_OVER_EXT = 0, VK_BLEND_OP_SRC_IN_EXT = 0, VK_BLEND_OP_DST_IN_EXT = 0, VK_BLEND_OP_SRC_OUT_EXT = 0, VK_BLEND_OP_DST_OUT_EXT = 0, VK_BLEND_OP_SRC_ATOP_EXT = 0, VK_BLEND_OP_DST_ATOP_EXT = 0, VK_BLEND_OP_XOR_EXT = 0, VK_BLEND_OP_MULTIPLY_EXT = 0, VK_BLEND_OP_SCREEN_EXT = 0, VK_BLEND_OP_OVERLAY_EXT = 0, VK_BLEND_OP_DARKEN_EXT = 0, VK_BLEND_OP_LIGHTEN_EXT = 0, VK_BLEND_OP_COLORDODGE_EXT = 0, VK_BLEND_OP_COLORBURN_EXT = 0, VK_BLEND_OP_HARDLIGHT_EXT = 0, VK_BLEND_OP_SOFTLIGHT_EXT = 0, VK_BLEND_OP_DIFFERENCE_EXT = 0, VK_BLEND_OP_EXCLUSION_EXT = 0, VK_BLEND_OP_INVERT_EXT = 0, VK_BLEND_OP_INVERT_RGB_EXT = 0, VK_BLEND_OP_LINEARDODGE_EXT = 0, VK_BLEND_OP_LINEARBURN_EXT = 0, VK_BLEND_OP_VIVIDLIGHT_EXT = 0, VK_BLEND_OP_LINEARLIGHT_EXT = 0, VK_BLEND_OP_PINLIGHT_EXT = 0, VK_BLEND_OP_HARDMIX_EXT = 0, VK_BLEND_OP_HSL_HUE_EXT = 0, VK_BLEND_OP_HSL_SATURATION_EXT = 0, VK_BLEND_OP_HSL_COLOR_EXT = 0, VK_BLEND_OP_HSL_LUMINOSITY_EXT = 0, VK_BLEND_OP_PLUS_EXT = 0, VK_BLEND_OP_PLUS_CLAMPED_EXT = 0, VK_BLEND_OP_PLUS_CLAMPED_ALPHA_EXT = 0, VK_BLEND_OP_PLUS_DARKER_EXT = 0, VK_BLEND_OP_MINUS_EXT = 0, VK_BLEND_OP_MINUS_CLAMPED_EXT = 0, VK_BLEND_OP_CONTRAST_EXT = 0, VK_BLEND_OP_INVERT_OVG_EXT = 0, VK_BLEND_OP_RED_EXT = 0, VK_BLEND_OP_GREEN_EXT = 0, VK_BLEND_OP_BLUE_EXT = 0, VK_BLEND_OP_MAX_ENUM = 0 };
enum VkBorderColor { VK_BORDER_COLOR_FLOAT_TRANSPARENT_BLACK = 0, VK_BORDER_COLOR_INT_TRANSPARENT_BLACK = 1, VK_BORDER_COLOR_FLOAT_OPAQUE_BLACK = 2, VK_BORDER_COLOR_INT_OPAQUE_BLACK = 3, VK_BORDER_COLOR_FLOAT_OPAQUE_WHITE = 4, VK_BORDER_COLOR_INT_OPAQUE_WHITE = 5, VK_BORDER_COLOR_FLOAT_CUSTOM_EXT = 0, VK_BORDER_COLOR_INT_CUSTOM_EXT = 0, VK_BORDER_COLOR_MAX_ENUM = 0 };
enum VkColorSpaceKHR { VK_COLOR_SPACE_SRGB_NONLINEAR_KHR = 0, VK_COLOR_SPACE_DISPLAY_P3_NONLINEAR_EXT = 0, VK_COLOR_SPACE_EXTENDED_SRGB_LINEAR_EXT = 0, VK_COLOR_SPACE_DISPLAY_P3_LINEAR_EXT = 0, VK_COLOR_SPACE_DCI_P3_NONLINEAR_EXT = 0, VK_COLOR_SPACE_BT709_LINEAR_EXT = 0, VK_COLOR_SPACE_BT709_NONLINEAR_EXT = 0, VK_COLOR_SPACE_BT2020_LINEAR_EXT = 0, VK_COLOR_SPACE_HDR10_ST2084_EXT = 0, VK_COLOR_SPACE_DOLBYVISION_EXT = 0, VK_COLOR_SPACE_HDR10_HLG_EXT = 0, VK_COLOR_SPACE_ADOBERGB_LINEAR_EXT = 0, VK_COLOR_SPACE_ADOBERGB_NONLINEAR_EXT = 0, VK_COLOR_SPACE_PASS_THROUGH_EXT = 0, VK_COLOR_SPACE_EXTENDED_SRGB_NONLINEAR_EXT = 0, VK_COLOR_SPACE_KHR_MAX_ENUM = 0, VK_COLORSPACE_SRGB_NONLINEAR_KHR = 0, VK_COLOR_SPACE_DCI_P3_LINEAR_EXT = 0 };
enum VkCommandBufferLevel { VK_COMMAND_BUFFER_LEVEL_PRIMARY = 0, VK_COMMAND_BUFFER_LEVEL_SECONDARY = 1, VK_COMMAND_BUFFER_LEVEL_MAX_ENUM = 0 };
enum VkCompareOp { VK_COMPARE_OP_NEVER = 0, VK_COMPARE_OP_LESS = 1, VK_COMPARE_OP_EQUAL = 2, VK_COMPARE_OP_LESS_OR_EQUAL = 3, VK_COMPARE_OP_GREATER = 4, VK_COMPARE_OP_NOT_EQUAL = 5, VK_COMPARE_OP_GREATER_OR_EQUAL = 6, VK_COMPARE_OP_ALWAYS = 7, VK_COMPARE_OP_MAX_ENUM = 0 };
enum VkComponentSwizzle { VK_COMPONENT_SWIZZLE_IDENTITY = 0, VK_COMPONENT_SWIZZLE_ZERO = 1, VK_COMPONENT_SWIZZLE_ONE = 2, VK_COMPONENT_SWIZZLE_R = 3, VK_COMPONENT_SWIZZLE_G = 4, VK_COMPONENT_SWIZZLE_B = 5, VK_COMPONENT_SWIZZLE_A = 6, VK_COMPONENT_SWIZZLE_MAX_ENUM = 0 };
enum VkCompositeAlphaFlagBitsKHR { VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR = 1, VK_COMPOSITE_ALPHA_PRE_MULTIPLIED_BIT_KHR = 2, VK_COMPOSITE_ALPHA_POST_MULTIPLIED_BIT_KHR = 4, VK_COMPOSITE_ALPHA_INHERIT_BIT_KHR = 8, VK_COMPOSITE_ALPHA_FLAG_BITS_KHR_MAX_ENUM = 0 };
enum VkDescriptorType { VK_DESCRIPTOR_TYPE_SAMPLER = 0, VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER = 1, VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE = 2, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE = 3, VK_DESCRIPTOR_TYPE_UNIFORM_TEXEL_BUFFER = 4, VK_DESCRIPTOR_TYPE_STORAGE_TEXEL_BUFFER = 5, VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER = 6, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER = 7, VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC = 8, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER_DYNAMIC = 9, VK_DESCRIPTOR_TYPE_INPUT_ATTACHMENT = 10, VK_DESCRIPTOR_TYPE_INLINE_UNIFORM_BLOCK = 0, VK_DESCRIPTOR_TYPE_ACCELERATION_STRUCTURE_KHR = 0, VK_DESCRIPTOR_TYPE_ACCELERATION_STRUCTURE_NV = 0, VK_DESCRIPTOR_TYPE_MUTABLE_EXT = 0, VK_DESCRIPTOR_TYPE_SAMPLE_WEIGHT_IMAGE_QCOM = 0, VK_DESCRIPTOR_TYPE_BLOCK_MATCH_IMAGE_QCOM = 0, VK_DESCRIPTOR_TYPE_TENSOR_ARM = 0, VK_DESCRIPTOR_TYPE_PARTITIONED_ACCELERATION_STRUCTURE_NV = 0, VK_DESCRIPTOR_TYPE_MAX_ENUM = 0, VK_DESCRIPTOR_TYPE_INLINE_UNIFORM_BLOCK_EXT = 0, VK_DESCRIPTOR_TYPE_MUTABLE_VALVE = 0 };
enum VkDynamicState { VK_DYNAMIC_STATE_VIEWPORT = 0, VK_DYNAMIC_STATE_SCISSOR = 1, VK_DYNAMIC_STATE_LINE_WIDTH = 2, VK_DYNAMIC_STATE_DEPTH_BIAS = 3, VK_DYNAMIC_STATE_BLEND_CONSTANTS = 4, VK_DYNAMIC_STATE_DEPTH_BOUNDS = 5, VK_DYNAMIC_STATE_STENCIL_COMPARE_MASK = 6, VK_DYNAMIC_STATE_STENCIL_WRITE_MASK = 7, VK_DYNAMIC_STATE_STENCIL_REFERENCE = 8, VK_DYNAMIC_STATE_VIEWPORT_W_SCALING_NV = 0, VK_DYNAMIC_STATE_DISCARD_RECTANGLE_EXT = 0, VK_DYNAMIC_STATE_DISCARD_RECTANGLE_ENABLE_EXT = 0, VK_DYNAMIC_STATE_DISCARD_RECTANGLE_MODE_EXT = 0, VK_DYNAMIC_STATE_SAMPLE_LOCATIONS_EXT = 0, VK_DYNAMIC_STATE_VIEWPORT_SHADING_RATE_PALETTE_NV = 0, VK_DYNAMIC_STATE_VIEWPORT_COARSE_SAMPLE_ORDER_NV = 0, VK_DYNAMIC_STATE_EXCLUSIVE_SCISSOR_ENABLE_NV = 0, VK_DYNAMIC_STATE_EXCLUSIVE_SCISSOR_NV = 0, VK_DYNAMIC_STATE_FRAGMENT_SHADING_RATE_KHR = 0, VK_DYNAMIC_STATE_LINE_STIPPLE = 0, VK_DYNAMIC_STATE_CULL_MODE = 0, VK_DYNAMIC_STATE_FRONT_FACE = 0, VK_DYNAMIC_STATE_PRIMITIVE_TOPOLOGY = 0, VK_DYNAMIC_STATE_VIEWPORT_WITH_COUNT = 0, VK_DYNAMIC_STATE_SCISSOR_WITH_COUNT = 0, VK_DYNAMIC_STATE_VERTEX_INPUT_BINDING_STRIDE = 0, VK_DYNAMIC_STATE_DEPTH_TEST_ENABLE = 0, VK_DYNAMIC_STATE_DEPTH_WRITE_ENABLE = 0, VK_DYNAMIC_STATE_DEPTH_COMPARE_OP = 0, VK_DYNAMIC_STATE_DEPTH_BOUNDS_TEST_ENABLE = 0, VK_DYNAMIC_STATE_STENCIL_TEST_ENABLE = 0, VK_DYNAMIC_STATE_STENCIL_OP = 0, VK_DYNAMIC_STATE_RAY_TRACING_PIPELINE_STACK_SIZE_KHR = 0, VK_DYNAMIC_STATE_VERTEX_INPUT_EXT = 0, VK_DYNAMIC_STATE_PATCH_CONTROL_POINTS_EXT = 0, VK_DYNAMIC_STATE_RASTERIZER_DISCARD_ENABLE = 0, VK_DYNAMIC_STATE_DEPTH_BIAS_ENABLE = 0, VK_DYNAMIC_STATE_LOGIC_OP_EXT = 0, VK_DYNAMIC_STATE_PRIMITIVE_RESTART_ENABLE = 0, VK_DYNAMIC_STATE_COLOR_WRITE_ENABLE_EXT = 0, VK_DYNAMIC_STATE_TESSELLATION_DOMAIN_ORIGIN_EXT = 0, VK_DYNAMIC_STATE_DEPTH_CLAMP_ENABLE_EXT = 0, VK_DYNAMIC_STATE_POLYGON_MODE_EXT = 0, VK_DYNAMIC_STATE_RASTERIZATION_SAMPLES_EXT = 0, VK_DYNAMIC_STATE_SAMPLE_MASK_EXT = 0, VK_DYNAMIC_STATE_ALPHA_TO_COVERAGE_ENABLE_EXT = 0, VK_DYNAMIC_STATE_ALPHA_TO_ONE_ENABLE_EXT = 0, VK_DYNAMIC_STATE_LOGIC_OP_ENABLE_EXT = 0, VK_DYNAMIC_STATE_COLOR_BLEND_ENABLE_EXT = 0, VK_DYNAMIC_STATE_COLOR_BLEND_EQUATION_EXT = 0, VK_DYNAMIC_STATE_COLOR_WRITE_MASK_EXT = 0, VK_DYNAMIC_STATE_RASTERIZATION_STREAM_EXT = 0, VK_DYNAMIC_STATE_CONSERVATIVE_RASTERIZATION_MODE_EXT = 0, VK_DYNAMIC_STATE_EXTRA_PRIMITIVE_OVERESTIMATION_SIZE_EXT = 0, VK_DYNAMIC_STATE_DEPTH_CLIP_ENABLE_EXT = 0, VK_DYNAMIC_STATE_SAMPLE_LOCATIONS_ENABLE_EXT = 0, VK_DYNAMIC_STATE_COLOR_BLEND_ADVANCED_EXT = 0, VK_DYNAMIC_STATE_PROVOKING_VERTEX_MODE_EXT = 0, VK_DYNAMIC_STATE_LINE_RASTERIZATION_MODE_EXT = 0, VK_DYNAMIC_STATE_LINE_STIPPLE_ENABLE_EXT = 0, VK_DYNAMIC_STATE_DEPTH_CLIP_NEGATIVE_ONE_TO_ONE_EXT = 0, VK_DYNAMIC_STATE_VIEWPORT_W_SCALING_ENABLE_NV = 0, VK_DYNAMIC_STATE_VIEWPORT_SWIZZLE_NV = 0, VK_DYNAMIC_STATE_COVERAGE_TO_COLOR_ENABLE_NV = 0, VK_DYNAMIC_STATE_COVERAGE_TO_COLOR_LOCATION_NV = 0, VK_DYNAMIC_STATE_COVERAGE_MODULATION_MODE_NV = 0, VK_DYNAMIC_STATE_COVERAGE_MODULATION_TABLE_ENABLE_NV = 0, VK_DYNAMIC_STATE_COVERAGE_MODULATION_TABLE_NV = 0, VK_DYNAMIC_STATE_SHADING_RATE_IMAGE_ENABLE_NV = 0, VK_DYNAMIC_STATE_REPRESENTATIVE_FRAGMENT_TEST_ENABLE_NV = 0, VK_DYNAMIC_STATE_COVERAGE_REDUCTION_MODE_NV = 0, VK_DYNAMIC_STATE_ATTACHMENT_FEEDBACK_LOOP_ENABLE_EXT = 0, VK_DYNAMIC_STATE_DEPTH_CLAMP_RANGE_EXT = 0, VK_DYNAMIC_STATE_MAX_ENUM = 0, VK_DYNAMIC_STATE_LINE_STIPPLE_EXT = 0, VK_DYNAMIC_STATE_CULL_MODE_EXT = 0, VK_DYNAMIC_STATE_FRONT_FACE_EXT = 0, VK_DYNAMIC_STATE_PRIMITIVE_TOPOLOGY_EXT = 0, VK_DYNAMIC_STATE_VIEWPORT_WITH_COUNT_EXT = 0, VK_DYNAMIC_STATE_SCISSOR_WITH_COUNT_EXT = 0, VK_DYNAMIC_STATE_VERTEX_INPUT_BINDING_STRIDE_EXT = 0, VK_DYNAMIC_STATE_DEPTH_TEST_ENABLE_EXT = 0, VK_DYNAMIC_STATE_DEPTH_WRITE_ENABLE_EXT = 0, VK_DYNAMIC_STATE_DEPTH_COMPARE_OP_EXT = 0, VK_DYNAMIC_STATE_DEPTH_BOUNDS_TEST_ENABLE_EXT = 0, VK_DYNAMIC_STATE_STENCIL_TEST_ENABLE_EXT = 0, VK_DYNAMIC_STATE_STENCIL_OP_EXT = 0, VK_DYNAMIC_STATE_RASTERIZER_DISCARD_ENABLE_EXT = 0, VK_DYNAMIC_STATE_DEPTH_BIAS_ENABLE_EXT = 0, VK_DYNAMIC_STATE_PRIMITIVE_RESTART_ENABLE_EXT = 0, VK_DYNAMIC_STATE_LINE_STIPPLE_KHR = 0 };
enum VkFilter { VK_FILTER_NEAREST = 0, VK_FILTER_LINEAR = 1, VK_FILTER_CUBIC_EXT = 0, VK_FILTER_MAX_ENUM = 0, VK_FILTER_CUBIC_IMG = 0 };
enum VkFormat { VK_FORMAT_UNDEFINED = 0, VK_FORMAT_R4G4_UNORM_PACK8 = 1, VK_FORMAT_R4G4B4A4_UNORM_PACK16 = 2, VK_FORMAT_B4G4R4A4_UNORM_PACK16 = 3, VK_FORMAT_R5G6B5_UNORM_PACK16 = 4, VK_FORMAT_B5G6R5_UNORM_PACK16 = 5, VK_FORMAT_R5G5B5A1_UNORM_PACK16 = 6, VK_FORMAT_B5G5R5A1_UNORM_PACK16 = 7, VK_FORMAT_A1R5G5B5_UNORM_PACK16 = 8, VK_FORMAT_R8_UNORM = 9, VK_FORMAT_R8_SNORM = 10, VK_FORMAT_R8_USCALED = 11, VK_FORMAT_R8_SSCALED = 12, VK_FORMAT_R8_UINT = 13, VK_FORMAT_R8_SINT = 14, VK_FORMAT_R8_SRGB = 15, VK_FORMAT_R8G8_UNORM = 16, VK_FORMAT_R8G8_SNORM = 17, VK_FORMAT_R8G8_USCALED = 18, VK_FORMAT_R8G8_SSCALED = 19, VK_FORMAT_R8G8_UINT = 20, VK_FORMAT_R8G8_SINT = 21, VK_FORMAT_R8G8_SRGB = 22, VK_FORMAT_R8G8B8_UNORM = 23, VK_FORMAT_R8G8B8_SNORM = 24, VK_FORMAT_R8G8B8_USCALED = 25, VK_FORMAT_R8G8B8_SSCALED = 26, VK_FORMAT_R8G8B8_UINT = 27, VK_FORMAT_R8G8B8_SINT = 28, VK_FORMAT_R8G8B8_SRGB = 29, VK_FORMAT_B8G8R8_UNORM = 30, VK_FORMAT_B8G8R8_SNORM = 31, VK_FORMAT_B8G8R8_USCALED = 32, VK_FORMAT_B8G8R8_SSCALED = 33, VK_FORMAT_B8G8R8_UINT = 34, VK_FORMAT_B8G8R8_SINT = 35, VK_FORMAT_B8G8R8_SRGB = 36, VK_FORMAT_R8G8B8A8_UNORM = 37, VK_FORMAT_R8G8B8A8_SNORM = 38, VK_FORMAT_R8G8B8A8_USCALED = 39, VK_FORMAT_R8G8B8A8_SSCALED = 40, VK_FORMAT_R8G8B8A8_UINT = 41, VK_FORMAT_R8G8B8A8_SINT = 42, VK_FORMAT_R8G8B8A8_SRGB = 43, VK_FORMAT_B8G8R8A8_UNORM = 44, VK_FORMAT_B8G8R8A8_SNORM = 45, VK_FORMAT_B8G8R8A8_USCALED = 46, VK_FORMAT_B8G8R8A8_SSCALED = 47, VK_FORMAT_B8G8R8A8_UINT = 48, VK_FORMAT_B8G8R8A8_SINT = 49, VK_FORMAT_B8G8R8A8_SRGB = 50, VK_FORMAT_A8B8G8R8_UNORM_PACK32 = 51, VK_FORMAT_A8B8G8R8_SNORM_PACK32 = 52, VK_FORMAT_A8B8G8R8_USCALED_PACK32 = 53, VK_FORMAT_A8B8G8R8_SSCALED_PACK32 = 54, VK_FORMAT_A8B8G8R8_UINT_PACK32 = 55, VK_FORMAT_A8B8G8R8_SINT_PACK32 = 56, VK_FORMAT_A8B8G8R8_SRGB_PACK32 = 57, VK_FORMAT_A2R10G10B10_UNORM_PACK32 = 58, VK_FORMAT_A2R10G10B10_SNORM_PACK32 = 59, VK_FORMAT_A2R10G10B10_USCALED_PACK32 = 60, VK_FORMAT_A2R10G10B10_SSCALED_PACK32 = 61, VK_FORMAT_A2R10G10B10_UINT_PACK32 = 62, VK_FORMAT_A2R10G10B10_SINT_PACK32 = 63, VK_FORMAT_A2B10G10R10_UNORM_PACK32 = 64, VK_FORMAT_A2B10G10R10_SNORM_PACK32 = 65, VK_FORMAT_A2B10G10R10_USCALED_PACK32 = 66, VK_FORMAT_A2B10G10R10_SSCALED_PACK32 = 67, VK_FORMAT_A2B10G10R10_UINT_PACK32 = 68, VK_FORMAT_A2B10G10R10_SINT_PACK32 = 69, VK_FORMAT_R16_UNORM = 70, VK_FORMAT_R16_SNORM = 71, VK_FORMAT_R16_USCALED = 72, VK_FORMAT_R16_SSCALED = 73, VK_FORMAT_R16_UINT = 74, VK_FORMAT_R16_SINT = 75, VK_FORMAT_R16_SFLOAT = 76, VK_FORMAT_R16G16_UNORM = 77, VK_FORMAT_R16G16_SNORM = 78, VK_FORMAT_R16G16_USCALED = 79, VK_FORMAT_R16G16_SSCALED = 80, VK_FORMAT_R16G16_UINT = 81, VK_FORMAT_R16G16_SINT = 82, VK_FORMAT_R16G16_SFLOAT = 83, VK_FORMAT_R16G16B16_UNORM = 84, VK_FORMAT_R16G16B16_SNORM = 85, VK_FORMAT_R16G16B16_USCALED = 86, VK_FORMAT_R16G16B16_SSCALED = 87, VK_FORMAT_R16G16B16_UINT = 88, VK_FORMAT_R16G16B16_SINT = 89, VK_FORMAT_R16G16B16_SFLOAT = 90, VK_FORMAT_R16G16B16A16_UNORM = 91, VK_FORMAT_R16G16B16A16_SNORM = 92, VK_FORMAT_R16G16B16A16_USCALED = 93, VK_FORMAT_R16G16B16A16_SSCALED = 94, VK_FORMAT_R16G16B16A16_UINT = 95, VK_FORMAT_R16G16B16A16_SINT = 96, VK_FORMAT_R16G16B16A16_SFLOAT = 97, VK_FORMAT_R32_UINT = 98, VK_FORMAT_R32_SINT = 99, VK_FORMAT_R32_SFLOAT = 100, VK_FORMAT_R32G32_UINT = 101, VK_FORMAT_R32G32_SINT = 102, VK_FORMAT_R32G32_SFLOAT = 103, VK_FORMAT_R32G32B32_UINT = 104, VK_FORMAT_R32G32B32_SINT = 105, VK_FORMAT_R32G32B32_SFLOAT = 106, VK_FORMAT_R32G32B32A32_UINT = 107, VK_FORMAT_R32G32B32A32_SINT = 108, VK_FORMAT_R32G32B32A32_SFLOAT = 109, VK_FORMAT_R64_UINT = 110, VK_FORMAT_R64_SINT = 111, VK_FORMAT_R64_SFLOAT = 112, VK_FORMAT_R64G64_UINT = 113, VK_FORMAT_R64G64_SINT = 114, VK_FORMAT_R64G64_SFLOAT = 115, VK_FORMAT_R64G64B64_UINT = 116, VK_FORMAT_R64G64B64_SINT = 117, VK_FORMAT_R64G64B64_SFLOAT = 118, VK_FORMAT_R64G64B64A64_UINT = 119, VK_FORMAT_R64G64B64A64_SINT = 120, VK_FORMAT_R64G64B64A64_SFLOAT = 121, VK_FORMAT_B10G11R11_UFLOAT_PACK32 = 122, VK_FORMAT_E5B9G9R9_UFLOAT_PACK32 = 123, VK_FORMAT_D16_UNORM = 124, VK_FORMAT_X8_D24_UNORM_PACK32 = 125, VK_FORMAT_D32_SFLOAT = 126, VK_FORMAT_S8_UINT = 127, VK_FORMAT_D16_UNORM_S8_UINT = 128, VK_FORMAT_D24_UNORM_S8_UINT = 129, VK_FORMAT_D32_SFLOAT_S8_UINT = 130, VK_FORMAT_BC1_RGB_UNORM_BLOCK = 131, VK_FORMAT_BC1_RGB_SRGB_BLOCK = 132, VK_FORMAT_BC1_RGBA_UNORM_BLOCK = 133, VK_FORMAT_BC1_RGBA_SRGB_BLOCK = 134, VK_FORMAT_BC2_UNORM_BLOCK = 135, VK_FORMAT_BC2_SRGB_BLOCK = 136, VK_FORMAT_BC3_UNORM_BLOCK = 137, VK_FORMAT_BC3_SRGB_BLOCK = 138, VK_FORMAT_BC4_UNORM_BLOCK = 139, VK_FORMAT_BC4_SNORM_BLOCK = 140, VK_FORMAT_BC5_UNORM_BLOCK = 141, VK_FORMAT_BC5_SNORM_BLOCK = 142, VK_FORMAT_BC6H_UFLOAT_BLOCK = 143, VK_FORMAT_BC6H_SFLOAT_BLOCK = 144, VK_FORMAT_BC7_UNORM_BLOCK = 145, VK_FORMAT_BC7_SRGB_BLOCK = 146, VK_FORMAT_ETC2_R8G8B8_UNORM_BLOCK = 147, VK_FORMAT_ETC2_R8G8B8_SRGB_BLOCK = 148, VK_FORMAT_ETC2_R8G8B8A1_UNORM_BLOCK = 149, VK_FORMAT_ETC2_R8G8B8A1_SRGB_BLOCK = 150, VK_FORMAT_ETC2_R8G8B8A8_UNORM_BLOCK = 151, VK_FORMAT_ETC2_R8G8B8A8_SRGB_BLOCK = 152, VK_FORMAT_EAC_R11_UNORM_BLOCK = 153, VK_FORMAT_EAC_R11_SNORM_BLOCK = 154, VK_FORMAT_EAC_R11G11_UNORM_BLOCK = 155, VK_FORMAT_EAC_R11G11_SNORM_BLOCK = 156, VK_FORMAT_ASTC_4x4_UNORM_BLOCK = 157, VK_FORMAT_ASTC_4x4_SRGB_BLOCK = 158, VK_FORMAT_ASTC_5x4_UNORM_BLOCK = 159, VK_FORMAT_ASTC_5x4_SRGB_BLOCK = 160, VK_FORMAT_ASTC_5x5_UNORM_BLOCK = 161, VK_FORMAT_ASTC_5x5_SRGB_BLOCK = 162, VK_FORMAT_ASTC_6x5_UNORM_BLOCK = 163, VK_FORMAT_ASTC_6x5_SRGB_BLOCK = 164, VK_FORMAT_ASTC_6x6_UNORM_BLOCK = 165, VK_FORMAT_ASTC_6x6_SRGB_BLOCK = 166, VK_FORMAT_ASTC_8x5_UNORM_BLOCK = 167, VK_FORMAT_ASTC_8x5_SRGB_BLOCK = 168, VK_FORMAT_ASTC_8x6_UNORM_BLOCK = 169, VK_FORMAT_ASTC_8x6_SRGB_BLOCK = 170, VK_FORMAT_ASTC_8x8_UNORM_BLOCK = 171, VK_FORMAT_ASTC_8x8_SRGB_BLOCK = 172, VK_FORMAT_ASTC_10x5_UNORM_BLOCK = 173, VK_FORMAT_ASTC_10x5_SRGB_BLOCK = 174, VK_FORMAT_ASTC_10x6_UNORM_BLOCK = 175, VK_FORMAT_ASTC_10x6_SRGB_BLOCK = 176, VK_FORMAT_ASTC_10x8_UNORM_BLOCK = 177, VK_FORMAT_ASTC_10x8_SRGB_BLOCK = 178, VK_FORMAT_ASTC_10x10_UNORM_BLOCK = 179, VK_FORMAT_ASTC_10x10_SRGB_BLOCK = 180, VK_FORMAT_ASTC_12x10_UNORM_BLOCK = 181, VK_FORMAT_ASTC_12x10_SRGB_BLOCK = 182, VK_FORMAT_ASTC_12x12_UNORM_BLOCK = 183, VK_FORMAT_ASTC_12x12_SRGB_BLOCK = 184, VK_FORMAT_PVRTC1_2BPP_UNORM_BLOCK_IMG = 0, VK_FORMAT_PVRTC1_4BPP_UNORM_BLOCK_IMG = 0, VK_FORMAT_PVRTC2_2BPP_UNORM_BLOCK_IMG = 0, VK_FORMAT_PVRTC2_4BPP_UNORM_BLOCK_IMG = 0, VK_FORMAT_PVRTC1_2BPP_SRGB_BLOCK_IMG = 0, VK_FORMAT_PVRTC1_4BPP_SRGB_BLOCK_IMG = 0, VK_FORMAT_PVRTC2_2BPP_SRGB_BLOCK_IMG = 0, VK_FORMAT_PVRTC2_4BPP_SRGB_BLOCK_IMG = 0, VK_FORMAT_ASTC_4x4_SFLOAT_BLOCK = 0, VK_FORMAT_ASTC_5x4_SFLOAT_BLOCK = 0, VK_FORMAT_ASTC_5x5_SFLOAT_BLOCK = 0, VK_FORMAT_ASTC_6x5_SFLOAT_BLOCK = 0, VK_FORMAT_ASTC_6x6_SFLOAT_BLOCK = 0, VK_FORMAT_ASTC_8x5_SFLOAT_BLOCK = 0, VK_FORMAT_ASTC_8x6_SFLOAT_BLOCK = 0, VK_FORMAT_ASTC_8x8_SFLOAT_BLOCK = 0, VK_FORMAT_ASTC_10x5_SFLOAT_BLOCK = 0, VK_FORMAT_ASTC_10x6_SFLOAT_BLOCK = 0, VK_FORMAT_ASTC_10x8_SFLOAT_BLOCK = 0, VK_FORMAT_ASTC_10x10_SFLOAT_BLOCK = 0, VK_FORMAT_ASTC_12x10_SFLOAT_BLOCK = 0, VK_FORMAT_ASTC_12x12_SFLOAT_BLOCK = 0, VK_FORMAT_G8B8G8R8_422_UNORM = 0, VK_FORMAT_B8G8R8G8_422_UNORM = 0, VK_FORMAT_G8_B8_R8_3PLANE_420_UNORM = 0, VK_FORMAT_G8_B8R8_2PLANE_420_UNORM = 0, VK_FORMAT_G8_B8_R8_3PLANE_422_UNORM = 0, VK_FORMAT_G8_B8R8_2PLANE_422_UNORM = 0, VK_FORMAT_G8_B8_R8_3PLANE_444_UNORM = 0, VK_FORMAT_R10X6_UNORM_PACK16 = 0, VK_FORMAT_R10X6G10X6_UNORM_2PACK16 = 0, VK_FORMAT_R10X6G10X6B10X6A10X6_UNORM_4PACK16 = 0, VK_FORMAT_G10X6B10X6G10X6R10X6_422_UNORM_4PACK16 = 0, VK_FORMAT_B10X6G10X6R10X6G10X6_422_UNORM_4PACK16 = 0, VK_FORMAT_G10X6_B10X6_R10X6_3PLANE_420_UNORM_3PACK16 = 0, VK_FORMAT_G10X6_B10X6R10X6_2PLANE_420_UNORM_3PACK16 = 0, VK_FORMAT_G10X6_B10X6_R10X6_3PLANE_422_UNORM_3PACK16 = 0, VK_FORMAT_G10X6_B10X6R10X6_2PLANE_422_UNORM_3PACK16 = 0, VK_FORMAT_G10X6_B10X6_R10X6_3PLANE_444_UNORM_3PACK16 = 0, VK_FORMAT_R12X4_UNORM_PACK16 = 0, VK_FORMAT_R12X4G12X4_UNORM_2PACK16 = 0, VK_FORMAT_R12X4G12X4B12X4A12X4_UNORM_4PACK16 = 0, VK_FORMAT_G12X4B12X4G12X4R12X4_422_UNORM_4PACK16 = 0, VK_FORMAT_B12X4G12X4R12X4G12X4_422_UNORM_4PACK16 = 0, VK_FORMAT_G12X4_B12X4_R12X4_3PLANE_420_UNORM_3PACK16 = 0, VK_FORMAT_G12X4_B12X4R12X4_2PLANE_420_UNORM_3PACK16 = 0, VK_FORMAT_G12X4_B12X4_R12X4_3PLANE_422_UNORM_3PACK16 = 0, VK_FORMAT_G12X4_B12X4R12X4_2PLANE_422_UNORM_3PACK16 = 0, VK_FORMAT_G12X4_B12X4_R12X4_3PLANE_444_UNORM_3PACK16 = 0, VK_FORMAT_G16B16G16R16_422_UNORM = 0, VK_FORMAT_B16G16R16G16_422_UNORM = 0, VK_FORMAT_G16_B16_R16_3PLANE_420_UNORM = 0, VK_FORMAT_G16_B16R16_2PLANE_420_UNORM = 0, VK_FORMAT_G16_B16_R16_3PLANE_422_UNORM = 0, VK_FORMAT_G16_B16R16_2PLANE_422_UNORM = 0, VK_FORMAT_G16_B16_R16_3PLANE_444_UNORM = 0, VK_FORMAT_G8_B8R8_2PLANE_444_UNORM = 0, VK_FORMAT_G10X6_B10X6R10X6_2PLANE_444_UNORM_3PACK16 = 0, VK_FORMAT_G12X4_B12X4R12X4_2PLANE_444_UNORM_3PACK16 = 0, VK_FORMAT_G16_B16R16_2PLANE_444_UNORM = 0, VK_FORMAT_A4R4G4B4_UNORM_PACK16 = 0, VK_FORMAT_A4B4G4R4_UNORM_PACK16 = 0, VK_FORMAT_R8_BOOL_ARM = 0, VK_FORMAT_R16G16_SFIXED5_NV = 0, VK_FORMAT_A1B5G5R5_UNORM_PACK16 = 0, VK_FORMAT_A8_UNORM = 0, VK_FORMAT_R10X6_UINT_PACK16_ARM = 0, VK_FORMAT_R10X6G10X6_UINT_2PACK16_ARM = 0, VK_FORMAT_R10X6G10X6B10X6A10X6_UINT_4PACK16_ARM = 0, VK_FORMAT_R12X4_UINT_PACK16_ARM = 0, VK_FORMAT_R12X4G12X4_UINT_2PACK16_ARM = 0, VK_FORMAT_R12X4G12X4B12X4A12X4_UINT_4PACK16_ARM = 0, VK_FORMAT_R14X2_UINT_PACK16_ARM = 0, VK_FORMAT_R14X2G14X2_UINT_2PACK16_ARM = 0, VK_FORMAT_R14X2G14X2B14X2A14X2_UINT_4PACK16_ARM = 0, VK_FORMAT_R14X2_UNORM_PACK16_ARM = 0, VK_FORMAT_R14X2G14X2_UNORM_2PACK16_ARM = 0, VK_FORMAT_R14X2G14X2B14X2A14X2_UNORM_4PACK16_ARM = 0, VK_FORMAT_G14X2_B14X2R14X2_2PLANE_420_UNORM_3PACK16_ARM = 0, VK_FORMAT_G14X2_B14X2R14X2_2PLANE_422_UNORM_3PACK16_ARM = 0, VK_FORMAT_MAX_ENUM = 0, VK_FORMAT_ASTC_4x4_SFLOAT_BLOCK_EXT = 0, VK_FORMAT_ASTC_5x4_SFLOAT_BLOCK_EXT = 0, VK_FORMAT_ASTC_5x5_SFLOAT_BLOCK_EXT = 0, VK_FORMAT_ASTC_6x5_SFLOAT_BLOCK_EXT = 0, VK_FORMAT_ASTC_6x6_SFLOAT_BLOCK_EXT = 0, VK_FORMAT_ASTC_8x5_SFLOAT_BLOCK_EXT = 0, VK_FORMAT_ASTC_8x6_SFLOAT_BLOCK_EXT = 0, VK_FORMAT_ASTC_8x8_SFLOAT_BLOCK_EXT = 0, VK_FORMAT_ASTC_10x5_SFLOAT_BLOCK_EXT = 0, VK_FORMAT_ASTC_10x6_SFLOAT_BLOCK_EXT = 0, VK_FORMAT_ASTC_10x8_SFLOAT_BLOCK_EXT = 0, VK_FORMAT_ASTC_10x10_SFLOAT_BLOCK_EXT = 0, VK_FORMAT_ASTC_12x10_SFLOAT_BLOCK_EXT = 0, VK_FORMAT_ASTC_12x12_SFLOAT_BLOCK_EXT = 0, VK_FORMAT_G8B8G8R8_422_UNORM_KHR = 0, VK_FORMAT_B8G8R8G8_422_UNORM_KHR = 0, VK_FORMAT_G8_B8_R8_3PLANE_420_UNORM_KHR = 0, VK_FORMAT_G8_B8R8_2PLANE_420_UNORM_KHR = 0, VK_FORMAT_G8_B8_R8_3PLANE_422_UNORM_KHR = 0, VK_FORMAT_G8_B8R8_2PLANE_422_UNORM_KHR = 0, VK_FORMAT_G8_B8_R8_3PLANE_444_UNORM_KHR = 0, VK_FORMAT_R10X6_UNORM_PACK16_KHR = 0, VK_FORMAT_R10X6G10X6_UNORM_2PACK16_KHR = 0, VK_FORMAT_R10X6G10X6B10X6A10X6_UNORM_4PACK16_KHR = 0, VK_FORMAT_G10X6B10X6G10X6R10X6_422_UNORM_4PACK16_KHR = 0, VK_FORMAT_B10X6G10X6R10X6G10X6_422_UNORM_4PACK16_KHR = 0, VK_FORMAT_G10X6_B10X6_R10X6_3PLANE_420_UNORM_3PACK16_KHR = 0, VK_FORMAT_G10X6_B10X6R10X6_2PLANE_420_UNORM_3PACK16_KHR = 0, VK_FORMAT_G10X6_B10X6_R10X6_3PLANE_422_UNORM_3PACK16_KHR = 0, VK_FORMAT_G10X6_B10X6R10X6_2PLANE_422_UNORM_3PACK16_KHR = 0, VK_FORMAT_G10X6_B10X6_R10X6_3PLANE_444_UNORM_3PACK16_KHR = 0, VK_FORMAT_R12X4_UNORM_PACK16_KHR = 0, VK_FORMAT_R12X4G12X4_UNORM_2PACK16_KHR = 0, VK_FORMAT_R12X4G12X4B12X4A12X4_UNORM_4PACK16_KHR = 0, VK_FORMAT_G12X4B12X4G12X4R12X4_422_UNORM_4PACK16_KHR = 0, VK_FORMAT_B12X4G12X4R12X4G12X4_422_UNORM_4PACK16_KHR = 0, VK_FORMAT_G12X4_B12X4_R12X4_3PLANE_420_UNORM_3PACK16_KHR = 0, VK_FORMAT_G12X4_B12X4R12X4_2PLANE_420_UNORM_3PACK16_KHR = 0, VK_FORMAT_G12X4_B12X4_R12X4_3PLANE_422_UNORM_3PACK16_KHR = 0, VK_FORMAT_G12X4_B12X4R12X4_2PLANE_422_UNORM_3PACK16_KHR = 0, VK_FORMAT_G12X4_B12X4_R12X4_3PLANE_444_UNORM_3PACK16_KHR = 0, VK_FORMAT_G16B16G16R16_422_UNORM_KHR = 0, VK_FORMAT_B16G16R16G16_422_UNORM_KHR = 0, VK_FORMAT_G16_B16_R16_3PLANE_420_UNORM_KHR = 0, VK_FORMAT_G16_B16R16_2PLANE_420_UNORM_KHR = 0, VK_FORMAT_G16_B16_R16_3PLANE_422_UNORM_KHR = 0, VK_FORMAT_G16_B16R16_2PLANE_422_UNORM_KHR = 0, VK_FORMAT_G16_B16_R16_3PLANE_444_UNORM_KHR = 0, VK_FORMAT_G8_B8R8_2PLANE_444_UNORM_EXT = 0, VK_FORMAT_G10X6_B10X6R10X6_2PLANE_444_UNORM_3PACK16_EXT = 0, VK_FORMAT_G12X4_B12X4R12X4_2PLANE_444_UNORM_3PACK16_EXT = 0, VK_FORMAT_G16_B16R16_2PLANE_444_UNORM_EXT = 0, VK_FORMAT_A4R4G4B4_UNORM_PACK16_EXT = 0, VK_FORMAT_A4B4G4R4_UNORM_PACK16_EXT = 0, VK_FORMAT_R16G16_S10_5_NV = 0, VK_FORMAT_A1B5G5R5_UNORM_PACK16_KHR = 0, VK_FORMAT_A8_UNORM_KHR = 0 };
enum VkFormatFeatureFlagBits { VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT = 1, VK_FORMAT_FEATURE_STORAGE_IMAGE_BIT = 2, VK_FORMAT_FEATURE_STORAGE_IMAGE_ATOMIC_BIT = 4, VK_FORMAT_FEATURE_UNIFORM_TEXEL_BUFFER_BIT = 8, VK_FORMAT_FEATURE_STORAGE_TEXEL_BUFFER_BIT = 16, VK_FORMAT_FEATURE_STORAGE_TEXEL_BUFFER_ATOMIC_BIT = 32, VK_FORMAT_FEATURE_VERTEX_BUFFER_BIT = 64, VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BIT = 128, VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BLEND_BIT = 256, VK_FORMAT_FEATURE_DEPTH_STENCIL_ATTACHMENT_BIT = 512, VK_FORMAT_FEATURE_BLIT_SRC_BIT = 1024, VK_FORMAT_FEATURE_BLIT_DST_BIT = 2048, VK_FORMAT_FEATURE_SAMPLED_IMAGE_FILTER_LINEAR_BIT = 4096, VK_FORMAT_FEATURE_SAMPLED_IMAGE_FILTER_CUBIC_BIT_EXT = 8192, VK_FORMAT_FEATURE_TRANSFER_SRC_BIT = 16384, VK_FORMAT_FEATURE_TRANSFER_DST_BIT = 32768, VK_FORMAT_FEATURE_SAMPLED_IMAGE_FILTER_MINMAX_BIT = 0, VK_FORMAT_FEATURE_MIDPOINT_CHROMA_SAMPLES_BIT = 0, VK_FORMAT_FEATURE_SAMPLED_IMAGE_YCBCR_CONVERSION_LINEAR_FILTER_BIT = 0, VK_FORMAT_FEATURE_SAMPLED_IMAGE_YCBCR_CONVERSION_SEPARATE_RECONSTRUCTION_FILTER_BIT = 0, VK_FORMAT_FEATURE_SAMPLED_IMAGE_YCBCR_CONVERSION_CHROMA_RECONSTRUCTION_EXPLICIT_BIT = 0, VK_FORMAT_FEATURE_SAMPLED_IMAGE_YCBCR_CONVERSION_CHROMA_RECONSTRUCTION_EXPLICIT_FORCEABLE_BIT = 0, VK_FORMAT_FEATURE_DISJOINT_BIT = 0, VK_FORMAT_FEATURE_COSITED_CHROMA_SAMPLES_BIT = 0, VK_FORMAT_FEATURE_FRAGMENT_DENSITY_MAP_BIT_EXT = 0, VK_FORMAT_FEATURE_VIDEO_DECODE_OUTPUT_BIT_KHR = 0, VK_FORMAT_FEATURE_VIDEO_DECODE_DPB_BIT_KHR = 0, VK_FORMAT_FEATURE_VIDEO_ENCODE_INPUT_BIT_KHR = 0, VK_FORMAT_FEATURE_VIDEO_ENCODE_DPB_BIT_KHR = 0, VK_FORMAT_FEATURE_ACCELERATION_STRUCTURE_VERTEX_BUFFER_BIT_KHR = 0, VK_FORMAT_FEATURE_FRAGMENT_SHADING_RATE_ATTACHMENT_BIT_KHR = 0, VK_FORMAT_FEATURE_FLAG_BITS_MAX_ENUM = 0, VK_FORMAT_FEATURE_SAMPLED_IMAGE_FILTER_CUBIC_BIT_IMG = 8192, VK_FORMAT_FEATURE_TRANSFER_SRC_BIT_KHR = 16384, VK_FORMAT_FEATURE_TRANSFER_DST_BIT_KHR = 32768, VK_FORMAT_FEATURE_SAMPLED_IMAGE_FILTER_MINMAX_BIT_EXT = 0, VK_FORMAT_FEATURE_MIDPOINT_CHROMA_SAMPLES_BIT_KHR = 0, VK_FORMAT_FEATURE_SAMPLED_IMAGE_YCBCR_CONVERSION_LINEAR_FILTER_BIT_KHR = 0, VK_FORMAT_FEATURE_SAMPLED_IMAGE_YCBCR_CONVERSION_SEPARATE_RECONSTRUCTION_FILTER_BIT_KHR = 0, VK_FORMAT_FEATURE_SAMPLED_IMAGE_YCBCR_CONVERSION_CHROMA_RECONSTRUCTION_EXPLICIT_BIT_KHR = 0, VK_FORMAT_FEATURE_SAMPLED_IMAGE_YCBCR_CONVERSION_CHROMA_RECONSTRUCTION_EXPLICIT_FORCEABLE_BIT_KHR = 0, VK_FORMAT_FEATURE_DISJOINT_BIT_KHR = 0, VK_FORMAT_FEATURE_COSITED_CHROMA_SAMPLES_BIT_KHR = 0 };
enum VkFrontFace { VK_FRONT_FACE_COUNTER_CLOCKWISE = 0, VK_FRONT_FACE_CLOCKWISE = 1, VK_FRONT_FACE_MAX_ENUM = 0 };
enum VkImageLayout { VK_IMAGE_LAYOUT_UNDEFINED = 0, VK_IMAGE_LAYOUT_GENERAL = 1, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL = 2, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL = 3, VK_IMAGE_LAYOUT_DEPTH_STENCIL_READ_ONLY_OPTIMAL = 4, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL = 5, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL = 6, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL = 7, VK_IMAGE_LAYOUT_PREINITIALIZED = 8, VK_IMAGE_LAYOUT_PRESENT_SRC_KHR = 0, VK_IMAGE_LAYOUT_VIDEO_DECODE_DST_KHR = 0, VK_IMAGE_LAYOUT_VIDEO_DECODE_SRC_KHR = 0, VK_IMAGE_LAYOUT_VIDEO_DECODE_DPB_KHR = 0, VK_IMAGE_LAYOUT_DEPTH_READ_ONLY_STENCIL_ATTACHMENT_OPTIMAL = 0, VK_IMAGE_LAYOUT_DEPTH_ATTACHMENT_STENCIL_READ_ONLY_OPTIMAL = 0, VK_IMAGE_LAYOUT_FRAGMENT_SHADING_RATE_ATTACHMENT_OPTIMAL_KHR = 0, VK_IMAGE_LAYOUT_FRAGMENT_DENSITY_MAP_OPTIMAL_EXT = 0, VK_IMAGE_LAYOUT_RENDERING_LOCAL_READ = 0, VK_IMAGE_LAYOUT_DEPTH_ATTACHMENT_OPTIMAL = 0, VK_IMAGE_LAYOUT_DEPTH_READ_ONLY_OPTIMAL = 0, VK_IMAGE_LAYOUT_STENCIL_ATTACHMENT_OPTIMAL = 0, VK_IMAGE_LAYOUT_STENCIL_READ_ONLY_OPTIMAL = 0, VK_IMAGE_LAYOUT_VIDEO_ENCODE_DST_KHR = 0, VK_IMAGE_LAYOUT_VIDEO_ENCODE_SRC_KHR = 0, VK_IMAGE_LAYOUT_VIDEO_ENCODE_DPB_KHR = 0, VK_IMAGE_LAYOUT_READ_ONLY_OPTIMAL = 0, VK_IMAGE_LAYOUT_ATTACHMENT_OPTIMAL = 0, VK_IMAGE_LAYOUT_ATTACHMENT_FEEDBACK_LOOP_OPTIMAL_EXT = 0, VK_IMAGE_LAYOUT_TENSOR_ALIASING_ARM = 0, VK_IMAGE_LAYOUT_VIDEO_ENCODE_QUANTIZATION_MAP_KHR = 0, VK_IMAGE_LAYOUT_ZERO_INITIALIZED_EXT = 0, VK_IMAGE_LAYOUT_MAX_ENUM = 0, VK_IMAGE_LAYOUT_DEPTH_READ_ONLY_STENCIL_ATTACHMENT_OPTIMAL_KHR = 0, VK_IMAGE_LAYOUT_DEPTH_ATTACHMENT_STENCIL_READ_ONLY_OPTIMAL_KHR = 0, VK_IMAGE_LAYOUT_SHADING_RATE_OPTIMAL_NV = 0, VK_IMAGE_LAYOUT_RENDERING_LOCAL_READ_KHR = 0, VK_IMAGE_LAYOUT_DEPTH_ATTACHMENT_OPTIMAL_KHR = 0, VK_IMAGE_LAYOUT_DEPTH_READ_ONLY_OPTIMAL_KHR = 0, VK_IMAGE_LAYOUT_STENCIL_ATTACHMENT_OPTIMAL_KHR = 0, VK_IMAGE_LAYOUT_STENCIL_READ_ONLY_OPTIMAL_KHR = 0, VK_IMAGE_LAYOUT_READ_ONLY_OPTIMAL_KHR = 0, VK_IMAGE_LAYOUT_ATTACHMENT_OPTIMAL_KHR = 0 };
enum VkImageTiling { VK_IMAGE_TILING_OPTIMAL = 0, VK_IMAGE_TILING_LINEAR = 1, VK_IMAGE_TILING_DRM_FORMAT_MODIFIER_EXT = 0, VK_IMAGE_TILING_MAX_ENUM = 0 };
enum VkImageType { VK_IMAGE_TYPE_1D = 0, VK_IMAGE_TYPE_2D = 1, VK_IMAGE_TYPE_3D = 2, VK_IMAGE_TYPE_MAX_ENUM = 0 };
enum VkImageUsageFlagBits { VK_IMAGE_USAGE_TRANSFER_SRC_BIT = 1, VK_IMAGE_USAGE_TRANSFER_DST_BIT = 2, VK_IMAGE_USAGE_SAMPLED_BIT = 4, VK_IMAGE_USAGE_STORAGE_BIT = 8, VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT = 16, VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT = 32, VK_IMAGE_USAGE_TRANSIENT_ATTACHMENT_BIT = 64, VK_IMAGE_USAGE_INPUT_ATTACHMENT_BIT = 128, VK_IMAGE_USAGE_FRAGMENT_SHADING_RATE_ATTACHMENT_BIT_KHR = 256, VK_IMAGE_USAGE_FRAGMENT_DENSITY_MAP_BIT_EXT = 512, VK_IMAGE_USAGE_VIDEO_DECODE_DST_BIT_KHR = 1024, VK_IMAGE_USAGE_VIDEO_DECODE_SRC_BIT_KHR = 2048, VK_IMAGE_USAGE_VIDEO_DECODE_DPB_BIT_KHR = 4096, VK_IMAGE_USAGE_VIDEO_ENCODE_DST_BIT_KHR = 8192, VK_IMAGE_USAGE_VIDEO_ENCODE_SRC_BIT_KHR = 16384, VK_IMAGE_USAGE_VIDEO_ENCODE_DPB_BIT_KHR = 32768, VK_IMAGE_USAGE_INVOCATION_MASK_BIT_HUAWEI = 0, VK_IMAGE_USAGE_ATTACHMENT_FEEDBACK_LOOP_BIT_EXT = 0, VK_IMAGE_USAGE_SAMPLE_WEIGHT_BIT_QCOM = 0, VK_IMAGE_USAGE_SAMPLE_BLOCK_MATCH_BIT_QCOM = 0, VK_IMAGE_USAGE_HOST_TRANSFER_BIT = 0, VK_IMAGE_USAGE_TENSOR_ALIASING_BIT_ARM = 0, VK_IMAGE_USAGE_VIDEO_ENCODE_QUANTIZATION_DELTA_MAP_BIT_KHR = 0, VK_IMAGE_USAGE_VIDEO_ENCODE_EMPHASIS_MAP_BIT_KHR = 0, VK_IMAGE_USAGE_TILE_MEMORY_BIT_QCOM = 0, VK_IMAGE_USAGE_FLAG_BITS_MAX_ENUM = 0, VK_IMAGE_USAGE_SHADING_RATE_IMAGE_BIT_NV = 256, VK_IMAGE_USAGE_HOST_TRANSFER_BIT_EXT = 0 };
enum VkImageViewType { VK_IMAGE_VIEW_TYPE_1D = 0, VK_IMAGE_VIEW_TYPE_2D = 1, VK_IMAGE_VIEW_TYPE_3D = 2, VK_IMAGE_VIEW_TYPE_CUBE = 3, VK_IMAGE_VIEW_TYPE_1D_ARRAY = 4, VK_IMAGE_VIEW_TYPE_2D_ARRAY = 5, VK_IMAGE_VIEW_TYPE_CUBE_ARRAY = 6, VK_IMAGE_VIEW_TYPE_MAX_ENUM = 0 };
enum VkIndexType { VK_INDEX_TYPE_UINT16 = 0, VK_INDEX_TYPE_UINT32 = 1, VK_INDEX_TYPE_NONE_KHR = 0, VK_INDEX_TYPE_UINT8 = 0, VK_INDEX_TYPE_MAX_ENUM = 0, VK_INDEX_TYPE_NONE_NV = 0, VK_INDEX_TYPE_UINT8_EXT = 0, VK_INDEX_TYPE_UINT8_KHR = 0 };
enum VkInternalAllocationType { VK_INTERNAL_ALLOCATION_TYPE_EXECUTABLE = 0, VK_INTERNAL_ALLOCATION_TYPE_MAX_ENUM = 0 };
enum VkLogicOp { VK_LOGIC_OP_CLEAR = 0, VK_LOGIC_OP_AND = 1, VK_LOGIC_OP_AND_REVERSE = 2, VK_LOGIC_OP_COPY = 3, VK_LOGIC_OP_AND_INVERTED = 4, VK_LOGIC_OP_NO_OP = 5, VK_LOGIC_OP_XOR = 6, VK_LOGIC_OP_OR = 7, VK_LOGIC_OP_NOR = 8, VK_LOGIC_OP_EQUIVALENT = 9, VK_LOGIC_OP_INVERT = 10, VK_LOGIC_OP_OR_REVERSE = 11, VK_LOGIC_OP_COPY_INVERTED = 12, VK_LOGIC_OP_OR_INVERTED = 13, VK_LOGIC_OP_NAND = 14, VK_LOGIC_OP_SET = 15, VK_LOGIC_OP_MAX_ENUM = 0 };
enum VkPhysicalDeviceType { VK_PHYSICAL_DEVICE_TYPE_OTHER = 0, VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU = 1, VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU = 2, VK_PHYSICAL_DEVICE_TYPE_VIRTUAL_GPU = 3, VK_PHYSICAL_DEVICE_TYPE_CPU = 4, VK_PHYSICAL_DEVICE_TYPE_MAX_ENUM = 0 };
enum VkPipelineBindPoint { VK_PIPELINE_BIND_POINT_GRAPHICS = 0, VK_PIPELINE_BIND_POINT_COMPUTE = 1, VK_PIPELINE_BIND_POINT_RAY_TRACING_KHR = 0, VK_PIPELINE_BIND_POINT_SUBPASS_SHADING_HUAWEI = 0, VK_PIPELINE_BIND_POINT_DATA_GRAPH_ARM = 0, VK_PIPELINE_BIND_POINT_MAX_ENUM = 0, VK_PIPELINE_BIND_POINT_RAY_TRACING_NV = 0 };
enum VkPipelineStageFlagBits { VK_PIPELINE_STAGE_NONE = 0, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT = 1, VK_PIPELINE_STAGE_DRAW_INDIRECT_BIT = 2, VK_PIPELINE_STAGE_VERTEX_INPUT_BIT = 4, VK_PIPELINE_STAGE_VERTEX_SHADER_BIT = 8, VK_PIPELINE_STAGE_TESSELLATION_CONTROL_SHADER_BIT = 16, VK_PIPELINE_STAGE_TESSELLATION_EVALUATION_SHADER_BIT = 32, VK_PIPELINE_STAGE_GEOMETRY_SHADER_BIT = 64, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT = 128, VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT = 256, VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT = 512, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT = 1024, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT = 2048, VK_PIPELINE_STAGE_TRANSFER_BIT = 4096, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT = 8192, VK_PIPELINE_STAGE_HOST_BIT = 16384, VK_PIPELINE_STAGE_ALL_GRAPHICS_BIT = 32768, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT = 0, VK_PIPELINE_STAGE_COMMAND_PREPROCESS_BIT_EXT = 0, VK_PIPELINE_STAGE_CONDITIONAL_RENDERING_BIT_EXT = 0, VK_PIPELINE_STAGE_TASK_SHADER_BIT_EXT = 0, VK_PIPELINE_STAGE_MESH_SHADER_BIT_EXT = 0, VK_PIPELINE_STAGE_RAY_TRACING_SHADER_BIT_KHR = 0, VK_PIPELINE_STAGE_FRAGMENT_SHADING_RATE_ATTACHMENT_BIT_KHR = 0, VK_PIPELINE_STAGE_FRAGMENT_DENSITY_PROCESS_BIT_EXT = 0, VK_PIPELINE_STAGE_TRANSFORM_FEEDBACK_BIT_EXT = 0, VK_PIPELINE_STAGE_ACCELERATION_STRUCTURE_BUILD_BIT_KHR = 0, VK_PIPELINE_STAGE_FLAG_BITS_MAX_ENUM = 0, VK_PIPELINE_STAGE_SHADING_RATE_IMAGE_BIT_NV = 0, VK_PIPELINE_STAGE_RAY_TRACING_SHADER_BIT_NV = 0, VK_PIPELINE_STAGE_ACCELERATION_STRUCTURE_BUILD_BIT_NV = 0, VK_PIPELINE_STAGE_TASK_SHADER_BIT_NV = 0, VK_PIPELINE_STAGE_MESH_SHADER_BIT_NV = 0, VK_PIPELINE_STAGE_COMMAND_PREPROCESS_BIT_NV = 0, VK_PIPELINE_STAGE_NONE_KHR = 0 };
enum VkPolygonMode { VK_POLYGON_MODE_FILL = 0, VK_POLYGON_MODE_LINE = 1, VK_POLYGON_MODE_POINT = 2, VK_POLYGON_MODE_FILL_RECTANGLE_NV = 0, VK_POLYGON_MODE_MAX_ENUM = 0 };
enum VkPresentModeKHR { VK_PRESENT_MODE_IMMEDIATE_KHR = 0, VK_PRESENT_MODE_MAILBOX_KHR = 1, VK_PRESENT_MODE_FIFO_KHR = 2, VK_PRESENT_MODE_FIFO_RELAXED_KHR = 3, VK_PRESENT_MODE_FIFO_LATEST_READY_KHR = 0, VK_PRESENT_MODE_KHR_MAX_ENUM = 0, VK_PRESENT_MODE_FIFO_LATEST_READY_EXT = 0 };
enum VkPrimitiveTopology { VK_PRIMITIVE_TOPOLOGY_POINT_LIST = 0, VK_PRIMITIVE_TOPOLOGY_LINE_LIST = 1, VK_PRIMITIVE_TOPOLOGY_LINE_STRIP = 2, VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST = 3, VK_PRIMITIVE_TOPOLOGY_TRIANGLE_STRIP = 4, VK_PRIMITIVE_TOPOLOGY_TRIANGLE_FAN = 5, VK_PRIMITIVE_TOPOLOGY_LINE_LIST_WITH_ADJACENCY = 6, VK_PRIMITIVE_TOPOLOGY_LINE_STRIP_WITH_ADJACENCY = 7, VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST_WITH_ADJACENCY = 8, VK_PRIMITIVE_TOPOLOGY_TRIANGLE_STRIP_WITH_ADJACENCY = 9, VK_PRIMITIVE_TOPOLOGY_PATCH_LIST = 10, VK_PRIMITIVE_TOPOLOGY_MAX_ENUM = 0 };
enum VkQueryType { VK_QUERY_TYPE_OCCLUSION = 0, VK_QUERY_TYPE_PIPELINE_STATISTICS = 1, VK_QUERY_TYPE_TIMESTAMP = 2, VK_QUERY_TYPE_RESULT_STATUS_ONLY_KHR = 0, VK_QUERY_TYPE_TRANSFORM_FEEDBACK_STREAM_EXT = 0, VK_QUERY_TYPE_PERFORMANCE_QUERY_KHR = 0, VK_QUERY_TYPE_ACCELERATION_STRUCTURE_COMPACTED_SIZE_KHR = 0, VK_QUERY_TYPE_ACCELERATION_STRUCTURE_SERIALIZATION_SIZE_KHR = 0, VK_QUERY_TYPE_ACCELERATION_STRUCTURE_COMPACTED_SIZE_NV = 0, VK_QUERY_TYPE_PERFORMANCE_QUERY_INTEL = 0, VK_QUERY_TYPE_VIDEO_ENCODE_FEEDBACK_KHR = 0, VK_QUERY_TYPE_MESH_PRIMITIVES_GENERATED_EXT = 0, VK_QUERY_TYPE_PRIMITIVES_GENERATED_EXT = 0, VK_QUERY_TYPE_ACCELERATION_STRUCTURE_SERIALIZATION_BOTTOM_LEVEL_POINTERS_KHR = 0, VK_QUERY_TYPE_ACCELERATION_STRUCTURE_SIZE_KHR = 0, VK_QUERY_TYPE_MICROMAP_SERIALIZATION_SIZE_EXT = 0, VK_QUERY_TYPE_MICROMAP_COMPACTED_SIZE_EXT = 0, VK_QUERY_TYPE_MAX_ENUM = 0 };
enum VkResult { VK_ERROR_NOT_ENOUGH_SPACE_KHR = -1000483000, VK_ERROR_COMPRESSION_EXHAUSTED_EXT = -1000338000, VK_ERROR_INVALID_VIDEO_STD_PARAMETERS_KHR = -1000299000, VK_ERROR_INVALID_OPAQUE_CAPTURE_ADDRESS = -1000257000, VK_ERROR_NOT_PERMITTED = -1000174001, VK_ERROR_FRAGMENTATION = -1000161000, VK_ERROR_INVALID_DRM_FORMAT_MODIFIER_PLANE_LAYOUT_EXT = -1000158000, VK_ERROR_INVALID_EXTERNAL_HANDLE = -1000072003, VK_ERROR_OUT_OF_POOL_MEMORY = -1000069000, VK_ERROR_VIDEO_STD_VERSION_NOT_SUPPORTED_KHR = -1000023005, VK_ERROR_VIDEO_PROFILE_CODEC_NOT_SUPPORTED_KHR = -1000023004, VK_ERROR_VIDEO_PROFILE_FORMAT_NOT_SUPPORTED_KHR = -1000023003, VK_ERROR_VIDEO_PROFILE_OPERATION_NOT_SUPPORTED_KHR = -1000023002, VK_ERROR_VIDEO_PICTURE_LAYOUT_NOT_SUPPORTED_KHR = -1000023001, VK_ERROR_IMAGE_USAGE_NOT_SUPPORTED_KHR = -1000023000, VK_ERROR_INVALID_SHADER_NV = -1000012000, VK_ERROR_VALIDATION_FAILED = -1000011001, VK_ERROR_OUT_OF_DATE_KHR = -1000001004, VK_ERROR_NATIVE_WINDOW_IN_USE_KHR = -1000000001, VK_ERROR_SURFACE_LOST_KHR = -1000000000, VK_ERROR_UNKNOWN = -13, VK_ERROR_FRAGMENTED_POOL = -12, VK_ERROR_FORMAT_NOT_SUPPORTED = -11, VK_ERROR_TOO_MANY_OBJECTS = -10, VK_ERROR_INCOMPATIBLE_DRIVER = -9, VK_ERROR_FEATURE_NOT_PRESENT = -8, VK_ERROR_EXTENSION_NOT_PRESENT = -7, VK_ERROR_LAYER_NOT_PRESENT = -6, VK_ERROR_MEMORY_MAP_FAILED = -5, VK_ERROR_DEVICE_LOST = -4, VK_ERROR_INITIALIZATION_FAILED = -3, VK_ERROR_OUT_OF_DEVICE_MEMORY = -2, VK_ERROR_OUT_OF_HOST_MEMORY = -1, VK_SUCCESS = 0, VK_NOT_READY = 1, VK_TIMEOUT = 2, VK_EVENT_SET = 3, VK_EVENT_RESET = 4, VK_INCOMPLETE = 5, VK_SUBOPTIMAL_KHR = 0, VK_THREAD_IDLE_KHR = 0, VK_THREAD_DONE_KHR = 0, VK_OPERATION_DEFERRED_KHR = 0, VK_OPERATION_NOT_DEFERRED_KHR = 0, VK_PIPELINE_COMPILE_REQUIRED = 0, VK_INCOMPATIBLE_SHADER_BINARY_EXT = 0, VK_PIPELINE_BINARY_MISSING_KHR = 0, VK_RESULT_MAX_ENUM = 0, VK_ERROR_VALIDATION_FAILED_EXT = -1000011001, VK_ERROR_OUT_OF_POOL_MEMORY_KHR = -1000069000, VK_ERROR_INVALID_EXTERNAL_HANDLE_KHR = -1000072003, VK_ERROR_FRAGMENTATION_EXT = -1000161000, VK_ERROR_NOT_PERMITTED_EXT = -1000174001, VK_ERROR_NOT_PERMITTED_KHR = -1000174001, VK_ERROR_INVALID_DEVICE_ADDRESS_EXT = -1000257000, VK_ERROR_INVALID_OPAQUE_CAPTURE_ADDRESS_KHR = -1000257000, VK_PIPELINE_COMPILE_REQUIRED_EXT = 0, VK_ERROR_PIPELINE_COMPILE_REQUIRED_EXT = 0, VK_ERROR_INCOMPATIBLE_SHADER_BINARY_EXT = 0 };
enum VkSampleCountFlagBits { VK_SAMPLE_COUNT_1_BIT = 1, VK_SAMPLE_COUNT_2_BIT = 2, VK_SAMPLE_COUNT_4_BIT = 4, VK_SAMPLE_COUNT_8_BIT = 8, VK_SAMPLE_COUNT_16_BIT = 16, VK_SAMPLE_COUNT_32_BIT = 32, VK_SAMPLE_COUNT_64_BIT = 64, VK_SAMPLE_COUNT_FLAG_BITS_MAX_ENUM = 0 };
enum VkSamplerAddressMode { VK_SAMPLER_ADDRESS_MODE_REPEAT = 0, VK_SAMPLER_ADDRESS_MODE_MIRRORED_REPEAT = 1, VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE = 2, VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_BORDER = 3, VK_SAMPLER_ADDRESS_MODE_MIRROR_CLAMP_TO_EDGE = 4, VK_SAMPLER_ADDRESS_MODE_MAX_ENUM = 0, VK_SAMPLER_ADDRESS_MODE_MIRROR_CLAMP_TO_EDGE_KHR = 4 };
enum VkSamplerMipmapMode { VK_SAMPLER_MIPMAP_MODE_NEAREST = 0, VK_SAMPLER_MIPMAP_MODE_LINEAR = 1, VK_SAMPLER_MIPMAP_MODE_MAX_ENUM = 0 };
enum VkShaderStageFlagBits { VK_SHADER_STAGE_VERTEX_BIT = 1, VK_SHADER_STAGE_TESSELLATION_CONTROL_BIT = 2, VK_SHADER_STAGE_TESSELLATION_EVALUATION_BIT = 4, VK_SHADER_STAGE_GEOMETRY_BIT = 8, VK_SHADER_STAGE_FRAGMENT_BIT = 16, VK_SHADER_STAGE_ALL_GRAPHICS = 31, VK_SHADER_STAGE_COMPUTE_BIT = 32, VK_SHADER_STAGE_TASK_BIT_EXT = 64, VK_SHADER_STAGE_MESH_BIT_EXT = 128, VK_SHADER_STAGE_RAYGEN_BIT_KHR = 256, VK_SHADER_STAGE_ANY_HIT_BIT_KHR = 512, VK_SHADER_STAGE_CLOSEST_HIT_BIT_KHR = 1024, VK_SHADER_STAGE_MISS_BIT_KHR = 2048, VK_SHADER_STAGE_INTERSECTION_BIT_KHR = 4096, VK_SHADER_STAGE_CALLABLE_BIT_KHR = 8192, VK_SHADER_STAGE_SUBPASS_SHADING_BIT_HUAWEI = 16384, VK_SHADER_STAGE_CLUSTER_CULLING_BIT_HUAWEI = 0, VK_SHADER_STAGE_ALL = 0, VK_SHADER_STAGE_RAYGEN_BIT_NV = 256, VK_SHADER_STAGE_ANY_HIT_BIT_NV = 512, VK_SHADER_STAGE_CLOSEST_HIT_BIT_NV = 1024, VK_SHADER_STAGE_MISS_BIT_NV = 2048, VK_SHADER_STAGE_INTERSECTION_BIT_NV = 4096, VK_SHADER_STAGE_CALLABLE_BIT_NV = 8192, VK_SHADER_STAGE_TASK_BIT_NV = 64, VK_SHADER_STAGE_MESH_BIT_NV = 128 };
enum VkSharingMode { VK_SHARING_MODE_EXCLUSIVE = 0, VK_SHARING_MODE_CONCURRENT = 1, VK_SHARING_MODE_MAX_ENUM = 0 };
enum VkStencilOp { VK_STENCIL_OP_KEEP = 0, VK_STENCIL_OP_ZERO = 1, VK_STENCIL_OP_REPLACE = 2, VK_STENCIL_OP_INCREMENT_AND_CLAMP = 3, VK_STENCIL_OP_DECREMENT_AND_CLAMP = 4, VK_STENCIL_OP_INVERT = 5, VK_STENCIL_OP_INCREMENT_AND_WRAP = 6, VK_STENCIL_OP_DECREMENT_AND_WRAP = 7, VK_STENCIL_OP_MAX_ENUM = 0 };
enum VkStructureType { VK_STRUCTURE_TYPE_APPLICATION_INFO = 0, VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO = 1, VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO = 2, VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO = 3, VK_STRUCTURE_TYPE_SUBMIT_INFO = 4, VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO = 5, VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE = 6, VK_STRUCTURE_TYPE_BIND_SPARSE_INFO = 7, VK_STRUCTURE_TYPE_FENCE_CREATE_INFO = 8, VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO = 9, VK_STRUCTURE_TYPE_EVENT_CREATE_INFO = 10, VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO = 11, VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO = 12, VK_STRUCTURE_TYPE_BUFFER_VIEW_CREATE_INFO = 13, VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO = 14, VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO = 15, VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO = 16, VK_STRUCTURE_TYPE_PIPELINE_CACHE_CREATE_INFO = 17, VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO = 18, VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO = 19, VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO = 20, VK_STRUCTURE_TYPE_PIPELINE_TESSELLATION_STATE_CREATE_INFO = 21, VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO = 22, VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO = 23, VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO = 24, VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO = 25, VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO = 26, VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO = 27, VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO = 28, VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO = 29, VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO = 30, VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO = 31, VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO = 32, VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO = 33, VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO = 34, VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET = 35, VK_STRUCTURE_TYPE_COPY_DESCRIPTOR_SET = 36, VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO = 37, VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO = 38, VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO = 39, VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO = 40, VK_STRUCTURE_TYPE_COMMAND_BUFFER_INHERITANCE_INFO = 41, VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO = 42, VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO = 43, VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER = 44, VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER = 45, VK_STRUCTURE_TYPE_MEMORY_BARRIER = 46, VK_STRUCTURE_TYPE_LOADER_INSTANCE_CREATE_INFO = 47, VK_STRUCTURE_TYPE_LOADER_DEVICE_CREATE_INFO = 48, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_1_FEATURES = 49, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_1_PROPERTIES = 50, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_2_FEATURES = 51, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_2_PROPERTIES = 52, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_3_FEATURES = 53, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_3_PROPERTIES = 54, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_4_FEATURES = 55, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_4_PROPERTIES = 56, VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PRESENT_INFO_KHR = 0, VK_STRUCTURE_TYPE_XLIB_SURFACE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_WAYLAND_SURFACE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_WIN32_SURFACE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_DEBUG_REPORT_CALLBACK_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_RASTERIZATION_ORDER_AMD = 0, VK_STRUCTURE_TYPE_DEBUG_MARKER_OBJECT_NAME_INFO_EXT = 0, VK_STRUCTURE_TYPE_DEBUG_MARKER_OBJECT_TAG_INFO_EXT = 0, VK_STRUCTURE_TYPE_DEBUG_MARKER_MARKER_INFO_EXT = 0, VK_STRUCTURE_TYPE_VIDEO_PROFILE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_CAPABILITIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_PICTURE_RESOURCE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_SESSION_MEMORY_REQUIREMENTS_KHR = 0, VK_STRUCTURE_TYPE_BIND_VIDEO_SESSION_MEMORY_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_SESSION_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_SESSION_PARAMETERS_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_SESSION_PARAMETERS_UPDATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_BEGIN_CODING_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_END_CODING_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_CODING_CONTROL_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_REFERENCE_SLOT_INFO_KHR = 0, VK_STRUCTURE_TYPE_QUEUE_FAMILY_VIDEO_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_PROFILE_LIST_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VIDEO_FORMAT_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_FORMAT_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_QUEUE_FAMILY_QUERY_RESULT_STATUS_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_CAPABILITIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_USAGE_INFO_KHR = 0, VK_STRUCTURE_TYPE_DEDICATED_ALLOCATION_IMAGE_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_DEDICATED_ALLOCATION_BUFFER_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_DEDICATED_ALLOCATION_MEMORY_ALLOCATE_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TRANSFORM_FEEDBACK_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TRANSFORM_FEEDBACK_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_STREAM_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_CU_MODULE_CREATE_INFO_NVX = 0, VK_STRUCTURE_TYPE_CU_FUNCTION_CREATE_INFO_NVX = 0, VK_STRUCTURE_TYPE_CU_LAUNCH_INFO_NVX = 0, VK_STRUCTURE_TYPE_CU_MODULE_TEXTURING_MODE_CREATE_INFO_NVX = 0, VK_STRUCTURE_TYPE_IMAGE_VIEW_HANDLE_INFO_NVX = 0, VK_STRUCTURE_TYPE_IMAGE_VIEW_ADDRESS_PROPERTIES_NVX = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_CAPABILITIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_SESSION_PARAMETERS_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_SESSION_PARAMETERS_ADD_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_PICTURE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_DPB_SLOT_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_NALU_SLICE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_GOP_REMAINING_FRAME_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_PROFILE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_RATE_CONTROL_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_RATE_CONTROL_LAYER_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_SESSION_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_QUALITY_LEVEL_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_SESSION_PARAMETERS_GET_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_SESSION_PARAMETERS_FEEDBACK_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_H264_CAPABILITIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_H264_PICTURE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_H264_PROFILE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_H264_SESSION_PARAMETERS_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_H264_SESSION_PARAMETERS_ADD_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_H264_DPB_SLOT_INFO_KHR = 0, VK_STRUCTURE_TYPE_TEXTURE_LOD_GATHER_FORMAT_PROPERTIES_AMD = 0, VK_STRUCTURE_TYPE_RENDERING_INFO = 0, VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_INFO = 0, VK_STRUCTURE_TYPE_PIPELINE_RENDERING_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DYNAMIC_RENDERING_FEATURES = 0, VK_STRUCTURE_TYPE_COMMAND_BUFFER_INHERITANCE_RENDERING_INFO = 0, VK_STRUCTURE_TYPE_RENDERING_FRAGMENT_SHADING_RATE_ATTACHMENT_INFO_KHR = 0, VK_STRUCTURE_TYPE_RENDERING_FRAGMENT_DENSITY_MAP_ATTACHMENT_INFO_EXT = 0, VK_STRUCTURE_TYPE_ATTACHMENT_SAMPLE_COUNT_INFO_AMD = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_CORNER_SAMPLED_IMAGE_FEATURES_NV = 0, VK_STRUCTURE_TYPE_RENDER_PASS_MULTIVIEW_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MULTIVIEW_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MULTIVIEW_PROPERTIES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2 = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2 = 0, VK_STRUCTURE_TYPE_FORMAT_PROPERTIES_2 = 0, VK_STRUCTURE_TYPE_IMAGE_FORMAT_PROPERTIES_2 = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_FORMAT_INFO_2 = 0, VK_STRUCTURE_TYPE_QUEUE_FAMILY_PROPERTIES_2 = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MEMORY_PROPERTIES_2 = 0, VK_STRUCTURE_TYPE_SPARSE_IMAGE_FORMAT_PROPERTIES_2 = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SPARSE_IMAGE_FORMAT_INFO_2 = 0, VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_FLAGS_INFO = 0, VK_STRUCTURE_TYPE_DEVICE_GROUP_RENDER_PASS_BEGIN_INFO = 0, VK_STRUCTURE_TYPE_DEVICE_GROUP_COMMAND_BUFFER_BEGIN_INFO = 0, VK_STRUCTURE_TYPE_DEVICE_GROUP_SUBMIT_INFO = 0, VK_STRUCTURE_TYPE_DEVICE_GROUP_BIND_SPARSE_INFO = 0, VK_STRUCTURE_TYPE_DEVICE_GROUP_PRESENT_CAPABILITIES_KHR = 0, VK_STRUCTURE_TYPE_IMAGE_SWAPCHAIN_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_BIND_IMAGE_MEMORY_SWAPCHAIN_INFO_KHR = 0, VK_STRUCTURE_TYPE_ACQUIRE_NEXT_IMAGE_INFO_KHR = 0, VK_STRUCTURE_TYPE_DEVICE_GROUP_PRESENT_INFO_KHR = 0, VK_STRUCTURE_TYPE_DEVICE_GROUP_SWAPCHAIN_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_BIND_BUFFER_MEMORY_DEVICE_GROUP_INFO = 0, VK_STRUCTURE_TYPE_BIND_IMAGE_MEMORY_DEVICE_GROUP_INFO = 0, VK_STRUCTURE_TYPE_VALIDATION_FLAGS_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_DRAW_PARAMETERS_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TEXTURE_COMPRESSION_ASTC_HDR_FEATURES = 0, VK_STRUCTURE_TYPE_IMAGE_VIEW_ASTC_DECODE_MODE_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ASTC_DECODE_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_ROBUSTNESS_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PIPELINE_ROBUSTNESS_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PIPELINE_ROBUSTNESS_PROPERTIES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_GROUP_PROPERTIES = 0, VK_STRUCTURE_TYPE_DEVICE_GROUP_DEVICE_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_IMAGE_FORMAT_INFO = 0, VK_STRUCTURE_TYPE_EXTERNAL_IMAGE_FORMAT_PROPERTIES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_BUFFER_INFO = 0, VK_STRUCTURE_TYPE_EXTERNAL_BUFFER_PROPERTIES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ID_PROPERTIES = 0, VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_BUFFER_CREATE_INFO = 0, VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO = 0, VK_STRUCTURE_TYPE_EXPORT_MEMORY_ALLOCATE_INFO = 0, VK_STRUCTURE_TYPE_IMPORT_MEMORY_WIN32_HANDLE_INFO_KHR = 0, VK_STRUCTURE_TYPE_EXPORT_MEMORY_WIN32_HANDLE_INFO_KHR = 0, VK_STRUCTURE_TYPE_MEMORY_WIN32_HANDLE_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_MEMORY_GET_WIN32_HANDLE_INFO_KHR = 0, VK_STRUCTURE_TYPE_IMPORT_MEMORY_FD_INFO_KHR = 0, VK_STRUCTURE_TYPE_MEMORY_FD_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_MEMORY_GET_FD_INFO_KHR = 0, VK_STRUCTURE_TYPE_WIN32_KEYED_MUTEX_ACQUIRE_RELEASE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_SEMAPHORE_INFO = 0, VK_STRUCTURE_TYPE_EXTERNAL_SEMAPHORE_PROPERTIES = 0, VK_STRUCTURE_TYPE_EXPORT_SEMAPHORE_CREATE_INFO = 0, VK_STRUCTURE_TYPE_IMPORT_SEMAPHORE_WIN32_HANDLE_INFO_KHR = 0, VK_STRUCTURE_TYPE_EXPORT_SEMAPHORE_WIN32_HANDLE_INFO_KHR = 0, VK_STRUCTURE_TYPE_D3D12_FENCE_SUBMIT_INFO_KHR = 0, VK_STRUCTURE_TYPE_SEMAPHORE_GET_WIN32_HANDLE_INFO_KHR = 0, VK_STRUCTURE_TYPE_IMPORT_SEMAPHORE_FD_INFO_KHR = 0, VK_STRUCTURE_TYPE_SEMAPHORE_GET_FD_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PUSH_DESCRIPTOR_PROPERTIES = 0, VK_STRUCTURE_TYPE_COMMAND_BUFFER_INHERITANCE_CONDITIONAL_RENDERING_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_CONDITIONAL_RENDERING_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_CONDITIONAL_RENDERING_BEGIN_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_FLOAT16_INT8_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_16BIT_STORAGE_FEATURES = 0, VK_STRUCTURE_TYPE_PRESENT_REGIONS_KHR = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_UPDATE_TEMPLATE_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_W_SCALING_STATE_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SUBGROUP_PROPERTIES = 0, VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_SWIZZLE_STATE_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DISCARD_RECTANGLE_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_DISCARD_RECTANGLE_STATE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_CONSERVATIVE_RASTERIZATION_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_CONSERVATIVE_STATE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DEPTH_CLIP_ENABLE_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_DEPTH_CLIP_STATE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_HDR_METADATA_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGELESS_FRAMEBUFFER_FEATURES = 0, VK_STRUCTURE_TYPE_FRAMEBUFFER_ATTACHMENTS_CREATE_INFO = 0, VK_STRUCTURE_TYPE_FRAMEBUFFER_ATTACHMENT_IMAGE_INFO = 0, VK_STRUCTURE_TYPE_RENDER_PASS_ATTACHMENT_BEGIN_INFO = 0, VK_STRUCTURE_TYPE_ATTACHMENT_DESCRIPTION_2 = 0, VK_STRUCTURE_TYPE_ATTACHMENT_REFERENCE_2 = 0, VK_STRUCTURE_TYPE_SUBPASS_DESCRIPTION_2 = 0, VK_STRUCTURE_TYPE_SUBPASS_DEPENDENCY_2 = 0, VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO_2 = 0, VK_STRUCTURE_TYPE_SUBPASS_BEGIN_INFO = 0, VK_STRUCTURE_TYPE_SUBPASS_END_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RELAXED_LINE_RASTERIZATION_FEATURES_IMG = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_FENCE_INFO = 0, VK_STRUCTURE_TYPE_EXTERNAL_FENCE_PROPERTIES = 0, VK_STRUCTURE_TYPE_EXPORT_FENCE_CREATE_INFO = 0, VK_STRUCTURE_TYPE_IMPORT_FENCE_WIN32_HANDLE_INFO_KHR = 0, VK_STRUCTURE_TYPE_EXPORT_FENCE_WIN32_HANDLE_INFO_KHR = 0, VK_STRUCTURE_TYPE_FENCE_GET_WIN32_HANDLE_INFO_KHR = 0, VK_STRUCTURE_TYPE_IMPORT_FENCE_FD_INFO_KHR = 0, VK_STRUCTURE_TYPE_FENCE_GET_FD_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PERFORMANCE_QUERY_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PERFORMANCE_QUERY_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_QUERY_POOL_PERFORMANCE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PERFORMANCE_QUERY_SUBMIT_INFO_KHR = 0, VK_STRUCTURE_TYPE_ACQUIRE_PROFILING_LOCK_INFO_KHR = 0, VK_STRUCTURE_TYPE_PERFORMANCE_COUNTER_KHR = 0, VK_STRUCTURE_TYPE_PERFORMANCE_COUNTER_DESCRIPTION_KHR = 0, VK_STRUCTURE_TYPE_PERFORMANCE_QUERY_RESERVATION_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_POINT_CLIPPING_PROPERTIES = 0, VK_STRUCTURE_TYPE_RENDER_PASS_INPUT_ATTACHMENT_ASPECT_CREATE_INFO = 0, VK_STRUCTURE_TYPE_IMAGE_VIEW_USAGE_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PIPELINE_TESSELLATION_DOMAIN_ORIGIN_STATE_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SURFACE_INFO_2_KHR = 0, VK_STRUCTURE_TYPE_SURFACE_CAPABILITIES_2_KHR = 0, VK_STRUCTURE_TYPE_SURFACE_FORMAT_2_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VARIABLE_POINTERS_FEATURES = 0, VK_STRUCTURE_TYPE_MACOS_SURFACE_CREATE_INFO_MVK = 0, VK_STRUCTURE_TYPE_MEMORY_DEDICATED_REQUIREMENTS = 0, VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO = 0, VK_STRUCTURE_TYPE_DEBUG_UTILS_OBJECT_NAME_INFO_EXT = 0, VK_STRUCTURE_TYPE_DEBUG_UTILS_OBJECT_TAG_INFO_EXT = 0, VK_STRUCTURE_TYPE_DEBUG_UTILS_LABEL_EXT = 0, VK_STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CALLBACK_DATA_EXT = 0, VK_STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SAMPLER_FILTER_MINMAX_PROPERTIES = 0, VK_STRUCTURE_TYPE_SAMPLER_REDUCTION_MODE_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_INLINE_UNIFORM_BLOCK_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_INLINE_UNIFORM_BLOCK_PROPERTIES = 0, VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET_INLINE_UNIFORM_BLOCK = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_INLINE_UNIFORM_BLOCK_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_BFLOAT16_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_SAMPLE_LOCATIONS_INFO_EXT = 0, VK_STRUCTURE_TYPE_RENDER_PASS_SAMPLE_LOCATIONS_BEGIN_INFO_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_SAMPLE_LOCATIONS_STATE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SAMPLE_LOCATIONS_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_MULTISAMPLE_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PROTECTED_SUBMIT_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROTECTED_MEMORY_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROTECTED_MEMORY_PROPERTIES = 0, VK_STRUCTURE_TYPE_DEVICE_QUEUE_INFO_2 = 0, VK_STRUCTURE_TYPE_BUFFER_MEMORY_REQUIREMENTS_INFO_2 = 0, VK_STRUCTURE_TYPE_IMAGE_MEMORY_REQUIREMENTS_INFO_2 = 0, VK_STRUCTURE_TYPE_IMAGE_SPARSE_MEMORY_REQUIREMENTS_INFO_2 = 0, VK_STRUCTURE_TYPE_MEMORY_REQUIREMENTS_2 = 0, VK_STRUCTURE_TYPE_SPARSE_IMAGE_MEMORY_REQUIREMENTS_2 = 0, VK_STRUCTURE_TYPE_IMAGE_FORMAT_LIST_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_BLEND_OPERATION_ADVANCED_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_BLEND_OPERATION_ADVANCED_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_ADVANCED_STATE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_COVERAGE_TO_COLOR_STATE_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_BUILD_GEOMETRY_INFO_KHR = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_DEVICE_ADDRESS_INFO_KHR = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_GEOMETRY_AABBS_DATA_KHR = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_GEOMETRY_INSTANCES_DATA_KHR = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_GEOMETRY_TRIANGLES_DATA_KHR = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_GEOMETRY_KHR = 0, VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET_ACCELERATION_STRUCTURE_KHR = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_VERSION_INFO_KHR = 0, VK_STRUCTURE_TYPE_COPY_ACCELERATION_STRUCTURE_INFO_KHR = 0, VK_STRUCTURE_TYPE_COPY_ACCELERATION_STRUCTURE_TO_MEMORY_INFO_KHR = 0, VK_STRUCTURE_TYPE_COPY_MEMORY_TO_ACCELERATION_STRUCTURE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ACCELERATION_STRUCTURE_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ACCELERATION_STRUCTURE_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_RAY_TRACING_PIPELINE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_RAY_TRACING_SHADER_GROUP_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_RAY_TRACING_PIPELINE_INTERFACE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_BUILD_SIZES_INFO_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_COVERAGE_MODULATION_STATE_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_SM_BUILTINS_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_SM_BUILTINS_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_SAMPLER_YCBCR_CONVERSION_CREATE_INFO = 0, VK_STRUCTURE_TYPE_SAMPLER_YCBCR_CONVERSION_INFO = 0, VK_STRUCTURE_TYPE_BIND_IMAGE_PLANE_MEMORY_INFO = 0, VK_STRUCTURE_TYPE_IMAGE_PLANE_MEMORY_REQUIREMENTS_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SAMPLER_YCBCR_CONVERSION_FEATURES = 0, VK_STRUCTURE_TYPE_SAMPLER_YCBCR_CONVERSION_IMAGE_FORMAT_PROPERTIES = 0, VK_STRUCTURE_TYPE_BIND_BUFFER_MEMORY_INFO = 0, VK_STRUCTURE_TYPE_BIND_IMAGE_MEMORY_INFO = 0, VK_STRUCTURE_TYPE_DRM_FORMAT_MODIFIER_PROPERTIES_LIST_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_DRM_FORMAT_MODIFIER_INFO_EXT = 0, VK_STRUCTURE_TYPE_IMAGE_DRM_FORMAT_MODIFIER_LIST_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_IMAGE_DRM_FORMAT_MODIFIER_EXPLICIT_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_IMAGE_DRM_FORMAT_MODIFIER_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_DRM_FORMAT_MODIFIER_PROPERTIES_LIST_2_EXT = 0, VK_STRUCTURE_TYPE_VALIDATION_CACHE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_SHADER_MODULE_VALIDATION_CACHE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_BINDING_FLAGS_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DESCRIPTOR_INDEXING_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DESCRIPTOR_INDEXING_PROPERTIES = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_SET_VARIABLE_DESCRIPTOR_COUNT_ALLOCATE_INFO = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_SET_VARIABLE_DESCRIPTOR_COUNT_LAYOUT_SUPPORT = 0, VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_SHADING_RATE_IMAGE_STATE_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADING_RATE_IMAGE_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADING_RATE_IMAGE_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_COARSE_SAMPLE_ORDER_STATE_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_RAY_TRACING_PIPELINE_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_GEOMETRY_NV = 0, VK_STRUCTURE_TYPE_GEOMETRY_TRIANGLES_NV = 0, VK_STRUCTURE_TYPE_GEOMETRY_AABB_NV = 0, VK_STRUCTURE_TYPE_BIND_ACCELERATION_STRUCTURE_MEMORY_INFO_NV = 0, VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET_ACCELERATION_STRUCTURE_NV = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_MEMORY_REQUIREMENTS_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_TRACING_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_RAY_TRACING_SHADER_GROUP_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_REPRESENTATIVE_FRAGMENT_TEST_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PIPELINE_REPRESENTATIVE_FRAGMENT_TEST_STATE_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_3_PROPERTIES = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_SUPPORT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_VIEW_IMAGE_FORMAT_INFO_EXT = 0, VK_STRUCTURE_TYPE_FILTER_CUBIC_IMAGE_VIEW_IMAGE_FORMAT_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_DEVICE_QUEUE_GLOBAL_PRIORITY_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_SUBGROUP_EXTENDED_TYPES_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_8BIT_STORAGE_FEATURES = 0, VK_STRUCTURE_TYPE_IMPORT_MEMORY_HOST_POINTER_INFO_EXT = 0, VK_STRUCTURE_TYPE_MEMORY_HOST_POINTER_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_MEMORY_HOST_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_ATOMIC_INT64_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_CLOCK_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_COMPILER_CONTROL_CREATE_INFO_AMD = 0, VK_STRUCTURE_TYPE_CALIBRATED_TIMESTAMP_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_CORE_PROPERTIES_AMD = 0, VK_STRUCTURE_TYPE_DEVICE_MEMORY_OVERALLOCATION_CREATE_INFO_AMD = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VERTEX_ATTRIBUTE_DIVISOR_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_DIVISOR_STATE_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VERTEX_ATTRIBUTE_DIVISOR_FEATURES = 0, VK_STRUCTURE_TYPE_PIPELINE_CREATION_FEEDBACK_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DRIVER_PROPERTIES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FLOAT_CONTROLS_PROPERTIES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DEPTH_STENCIL_RESOLVE_PROPERTIES = 0, VK_STRUCTURE_TYPE_SUBPASS_DESCRIPTION_DEPTH_STENCIL_RESOLVE = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COMPUTE_SHADER_DERIVATIVES_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MESH_SHADER_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MESH_SHADER_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_SHADER_BARYCENTRIC_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_IMAGE_FOOTPRINT_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_EXCLUSIVE_SCISSOR_STATE_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXCLUSIVE_SCISSOR_FEATURES_NV = 0, VK_STRUCTURE_TYPE_CHECKPOINT_DATA_NV = 0, VK_STRUCTURE_TYPE_QUEUE_FAMILY_CHECKPOINT_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TIMELINE_SEMAPHORE_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TIMELINE_SEMAPHORE_PROPERTIES = 0, VK_STRUCTURE_TYPE_SEMAPHORE_TYPE_CREATE_INFO = 0, VK_STRUCTURE_TYPE_TIMELINE_SEMAPHORE_SUBMIT_INFO = 0, VK_STRUCTURE_TYPE_SEMAPHORE_WAIT_INFO = 0, VK_STRUCTURE_TYPE_SEMAPHORE_SIGNAL_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_INTEGER_FUNCTIONS_2_FEATURES_INTEL = 0, VK_STRUCTURE_TYPE_QUERY_POOL_PERFORMANCE_QUERY_CREATE_INFO_INTEL = 0, VK_STRUCTURE_TYPE_INITIALIZE_PERFORMANCE_API_INFO_INTEL = 0, VK_STRUCTURE_TYPE_PERFORMANCE_MARKER_INFO_INTEL = 0, VK_STRUCTURE_TYPE_PERFORMANCE_STREAM_MARKER_INFO_INTEL = 0, VK_STRUCTURE_TYPE_PERFORMANCE_OVERRIDE_INFO_INTEL = 0, VK_STRUCTURE_TYPE_PERFORMANCE_CONFIGURATION_ACQUIRE_INFO_INTEL = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_MEMORY_MODEL_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PCI_BUS_INFO_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_TERMINATE_INVOCATION_FEATURES = 0, VK_STRUCTURE_TYPE_METAL_SURFACE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_DENSITY_MAP_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_DENSITY_MAP_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_RENDER_PASS_FRAGMENT_DENSITY_MAP_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SCALAR_BLOCK_LAYOUT_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SUBGROUP_SIZE_CONTROL_PROPERTIES = 0, VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_REQUIRED_SUBGROUP_SIZE_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SUBGROUP_SIZE_CONTROL_FEATURES = 0, VK_STRUCTURE_TYPE_FRAGMENT_SHADING_RATE_ATTACHMENT_INFO_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_FRAGMENT_SHADING_RATE_STATE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_SHADING_RATE_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_SHADING_RATE_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_SHADING_RATE_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_CORE_PROPERTIES_2_AMD = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COHERENT_MEMORY_FEATURES_AMD = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DYNAMIC_RENDERING_LOCAL_READ_FEATURES = 0, VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_LOCATION_INFO = 0, VK_STRUCTURE_TYPE_RENDERING_INPUT_ATTACHMENT_INDEX_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_IMAGE_ATOMIC_INT64_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_QUAD_CONTROL_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MEMORY_BUDGET_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MEMORY_PRIORITY_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_MEMORY_PRIORITY_ALLOCATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DEDICATED_ALLOCATION_IMAGE_ALIASING_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SEPARATE_DEPTH_STENCIL_LAYOUTS_FEATURES = 0, VK_STRUCTURE_TYPE_ATTACHMENT_REFERENCE_STENCIL_LAYOUT = 0, VK_STRUCTURE_TYPE_ATTACHMENT_DESCRIPTION_STENCIL_LAYOUT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_BUFFER_DEVICE_ADDRESS_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_BUFFER_DEVICE_ADDRESS_INFO = 0, VK_STRUCTURE_TYPE_BUFFER_DEVICE_ADDRESS_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TOOL_PROPERTIES = 0, VK_STRUCTURE_TYPE_IMAGE_STENCIL_USAGE_CREATE_INFO = 0, VK_STRUCTURE_TYPE_VALIDATION_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PRESENT_WAIT_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COOPERATIVE_MATRIX_FEATURES_NV = 0, VK_STRUCTURE_TYPE_COOPERATIVE_MATRIX_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COOPERATIVE_MATRIX_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COVERAGE_REDUCTION_MODE_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PIPELINE_COVERAGE_REDUCTION_STATE_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_FRAMEBUFFER_MIXED_SAMPLES_COMBINATION_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_SHADER_INTERLOCK_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_YCBCR_IMAGE_ARRAYS_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_UNIFORM_BUFFER_STANDARD_LAYOUT_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROVOKING_VERTEX_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_PROVOKING_VERTEX_STATE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROVOKING_VERTEX_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_HEADLESS_SURFACE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_BUFFER_DEVICE_ADDRESS_FEATURES = 0, VK_STRUCTURE_TYPE_BUFFER_OPAQUE_CAPTURE_ADDRESS_CREATE_INFO = 0, VK_STRUCTURE_TYPE_MEMORY_OPAQUE_CAPTURE_ADDRESS_ALLOCATE_INFO = 0, VK_STRUCTURE_TYPE_DEVICE_MEMORY_OPAQUE_CAPTURE_ADDRESS_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_LINE_RASTERIZATION_FEATURES = 0, VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_LINE_STATE_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_LINE_RASTERIZATION_PROPERTIES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_ATOMIC_FLOAT_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_HOST_QUERY_RESET_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_INDEX_TYPE_UINT8_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTENDED_DYNAMIC_STATE_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PIPELINE_EXECUTABLE_PROPERTIES_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_EXECUTABLE_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_EXECUTABLE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_EXECUTABLE_STATISTIC_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_EXECUTABLE_INTERNAL_REPRESENTATION_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_HOST_IMAGE_COPY_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_HOST_IMAGE_COPY_PROPERTIES = 0, VK_STRUCTURE_TYPE_MEMORY_TO_IMAGE_COPY = 0, VK_STRUCTURE_TYPE_IMAGE_TO_MEMORY_COPY = 0, VK_STRUCTURE_TYPE_COPY_IMAGE_TO_MEMORY_INFO = 0, VK_STRUCTURE_TYPE_COPY_MEMORY_TO_IMAGE_INFO = 0, VK_STRUCTURE_TYPE_HOST_IMAGE_LAYOUT_TRANSITION_INFO = 0, VK_STRUCTURE_TYPE_COPY_IMAGE_TO_IMAGE_INFO = 0, VK_STRUCTURE_TYPE_SUBRESOURCE_HOST_MEMCPY_SIZE = 0, VK_STRUCTURE_TYPE_HOST_IMAGE_COPY_DEVICE_PERFORMANCE_QUERY = 0, VK_STRUCTURE_TYPE_MEMORY_MAP_INFO = 0, VK_STRUCTURE_TYPE_MEMORY_UNMAP_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAP_MEMORY_PLACED_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAP_MEMORY_PLACED_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_MEMORY_MAP_PLACED_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_ATOMIC_FLOAT_2_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_SURFACE_PRESENT_MODE_KHR = 0, VK_STRUCTURE_TYPE_SURFACE_PRESENT_SCALING_CAPABILITIES_KHR = 0, VK_STRUCTURE_TYPE_SURFACE_PRESENT_MODE_COMPATIBILITY_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SWAPCHAIN_MAINTENANCE_1_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_SWAPCHAIN_PRESENT_FENCE_INFO_KHR = 0, VK_STRUCTURE_TYPE_SWAPCHAIN_PRESENT_MODES_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_SWAPCHAIN_PRESENT_MODE_INFO_KHR = 0, VK_STRUCTURE_TYPE_SWAPCHAIN_PRESENT_SCALING_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_RELEASE_SWAPCHAIN_IMAGES_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_DEMOTE_TO_HELPER_INVOCATION_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DEVICE_GENERATED_COMMANDS_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_GRAPHICS_SHADER_GROUP_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_SHADER_GROUPS_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_INDIRECT_COMMANDS_LAYOUT_TOKEN_NV = 0, VK_STRUCTURE_TYPE_INDIRECT_COMMANDS_LAYOUT_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_GENERATED_COMMANDS_INFO_NV = 0, VK_STRUCTURE_TYPE_GENERATED_COMMANDS_MEMORY_REQUIREMENTS_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DEVICE_GENERATED_COMMANDS_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_INHERITED_VIEWPORT_SCISSOR_FEATURES_NV = 0, VK_STRUCTURE_TYPE_COMMAND_BUFFER_INHERITANCE_VIEWPORT_SCISSOR_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_INTEGER_DOT_PRODUCT_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_INTEGER_DOT_PRODUCT_PROPERTIES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TEXEL_BUFFER_ALIGNMENT_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TEXEL_BUFFER_ALIGNMENT_PROPERTIES = 0, VK_STRUCTURE_TYPE_COMMAND_BUFFER_INHERITANCE_RENDER_PASS_TRANSFORM_INFO_QCOM = 0, VK_STRUCTURE_TYPE_RENDER_PASS_TRANSFORM_BEGIN_INFO_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DEPTH_BIAS_CONTROL_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_DEPTH_BIAS_INFO_EXT = 0, VK_STRUCTURE_TYPE_DEPTH_BIAS_REPRESENTATION_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ROBUSTNESS_2_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ROBUSTNESS_2_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_SAMPLER_CUSTOM_BORDER_COLOR_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_CUSTOM_BORDER_COLOR_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_CUSTOM_BORDER_COLOR_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_LIBRARY_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PRESENT_BARRIER_FEATURES_NV = 0, VK_STRUCTURE_TYPE_SURFACE_CAPABILITIES_PRESENT_BARRIER_NV = 0, VK_STRUCTURE_TYPE_SWAPCHAIN_PRESENT_BARRIER_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_PRESENT_ID_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PRESENT_ID_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PRIVATE_DATA_FEATURES = 0, VK_STRUCTURE_TYPE_DEVICE_PRIVATE_DATA_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PRIVATE_DATA_SLOT_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PIPELINE_CREATION_CACHE_CONTROL_FEATURES = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_RATE_CONTROL_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_RATE_CONTROL_LAYER_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_CAPABILITIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_USAGE_INFO_KHR = 0, VK_STRUCTURE_TYPE_QUERY_POOL_VIDEO_ENCODE_FEEDBACK_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VIDEO_ENCODE_QUALITY_LEVEL_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_QUALITY_LEVEL_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_QUALITY_LEVEL_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_SESSION_PARAMETERS_GET_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_SESSION_PARAMETERS_FEEDBACK_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DIAGNOSTICS_CONFIG_FEATURES_NV = 0, VK_STRUCTURE_TYPE_DEVICE_DIAGNOSTICS_CONFIG_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TILE_SHADING_FEATURES_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TILE_SHADING_PROPERTIES_QCOM = 0, VK_STRUCTURE_TYPE_RENDER_PASS_TILE_SHADING_CREATE_INFO_QCOM = 0, VK_STRUCTURE_TYPE_PER_TILE_BEGIN_INFO_QCOM = 0, VK_STRUCTURE_TYPE_PER_TILE_END_INFO_QCOM = 0, VK_STRUCTURE_TYPE_DISPATCH_TILE_INFO_QCOM = 0, VK_STRUCTURE_TYPE_QUERY_LOW_LATENCY_SUPPORT_NV = 0, VK_STRUCTURE_TYPE_MEMORY_BARRIER_2 = 0, VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER_2 = 0, VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2 = 0, VK_STRUCTURE_TYPE_DEPENDENCY_INFO = 0, VK_STRUCTURE_TYPE_SUBMIT_INFO_2 = 0, VK_STRUCTURE_TYPE_SEMAPHORE_SUBMIT_INFO = 0, VK_STRUCTURE_TYPE_COMMAND_BUFFER_SUBMIT_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SYNCHRONIZATION_2_FEATURES = 0, VK_STRUCTURE_TYPE_QUEUE_FAMILY_CHECKPOINT_PROPERTIES_2_NV = 0, VK_STRUCTURE_TYPE_CHECKPOINT_DATA_2_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DESCRIPTOR_BUFFER_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DESCRIPTOR_BUFFER_DENSITY_MAP_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DESCRIPTOR_BUFFER_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_ADDRESS_INFO_EXT = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_GET_INFO_EXT = 0, VK_STRUCTURE_TYPE_BUFFER_CAPTURE_DESCRIPTOR_DATA_INFO_EXT = 0, VK_STRUCTURE_TYPE_IMAGE_CAPTURE_DESCRIPTOR_DATA_INFO_EXT = 0, VK_STRUCTURE_TYPE_IMAGE_VIEW_CAPTURE_DESCRIPTOR_DATA_INFO_EXT = 0, VK_STRUCTURE_TYPE_SAMPLER_CAPTURE_DESCRIPTOR_DATA_INFO_EXT = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_CAPTURE_DESCRIPTOR_DATA_INFO_EXT = 0, VK_STRUCTURE_TYPE_OPAQUE_CAPTURE_DESCRIPTOR_DATA_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_BUFFER_BINDING_INFO_EXT = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_BUFFER_BINDING_PUSH_DESCRIPTOR_BUFFER_HANDLE_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_GRAPHICS_PIPELINE_LIBRARY_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_GRAPHICS_PIPELINE_LIBRARY_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_LIBRARY_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_EARLY_AND_LATE_FRAGMENT_TESTS_FEATURES_AMD = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_SHADER_BARYCENTRIC_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_SUBGROUP_UNIFORM_CONTROL_FLOW_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ZERO_INITIALIZE_WORKGROUP_MEMORY_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_SHADING_RATE_ENUMS_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_SHADING_RATE_ENUMS_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PIPELINE_FRAGMENT_SHADING_RATE_ENUM_STATE_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_GEOMETRY_MOTION_TRIANGLES_DATA_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_TRACING_MOTION_BLUR_FEATURES_NV = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_MOTION_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MESH_SHADER_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MESH_SHADER_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_YCBCR_2_PLANE_444_FORMATS_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_DENSITY_MAP_2_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_DENSITY_MAP_2_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_COPY_COMMAND_TRANSFORM_INFO_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_ROBUSTNESS_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_WORKGROUP_MEMORY_EXPLICIT_LAYOUT_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_COPY_BUFFER_INFO_2 = 0, VK_STRUCTURE_TYPE_COPY_IMAGE_INFO_2 = 0, VK_STRUCTURE_TYPE_COPY_BUFFER_TO_IMAGE_INFO_2 = 0, VK_STRUCTURE_TYPE_COPY_IMAGE_TO_BUFFER_INFO_2 = 0, VK_STRUCTURE_TYPE_BLIT_IMAGE_INFO_2 = 0, VK_STRUCTURE_TYPE_RESOLVE_IMAGE_INFO_2 = 0, VK_STRUCTURE_TYPE_BUFFER_COPY_2 = 0, VK_STRUCTURE_TYPE_IMAGE_COPY_2 = 0, VK_STRUCTURE_TYPE_IMAGE_BLIT_2 = 0, VK_STRUCTURE_TYPE_BUFFER_IMAGE_COPY_2 = 0, VK_STRUCTURE_TYPE_IMAGE_RESOLVE_2 = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_COMPRESSION_CONTROL_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_IMAGE_COMPRESSION_CONTROL_EXT = 0, VK_STRUCTURE_TYPE_SUBRESOURCE_LAYOUT_2 = 0, VK_STRUCTURE_TYPE_IMAGE_SUBRESOURCE_2 = 0, VK_STRUCTURE_TYPE_IMAGE_COMPRESSION_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ATTACHMENT_FEEDBACK_LOOP_LAYOUT_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_4444_FORMATS_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FAULT_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_DEVICE_FAULT_COUNTS_EXT = 0, VK_STRUCTURE_TYPE_DEVICE_FAULT_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RASTERIZATION_ORDER_ATTACHMENT_ACCESS_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RGBA10X6_FORMATS_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_TRACING_PIPELINE_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_TRACING_PIPELINE_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_QUERY_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MUTABLE_DESCRIPTOR_TYPE_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_MUTABLE_DESCRIPTOR_TYPE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VERTEX_INPUT_DYNAMIC_STATE_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_VERTEX_INPUT_BINDING_DESCRIPTION_2_EXT = 0, VK_STRUCTURE_TYPE_VERTEX_INPUT_ATTRIBUTE_DESCRIPTION_2_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ADDRESS_BINDING_REPORT_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_DEVICE_ADDRESS_BINDING_CALLBACK_DATA_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DEPTH_CLIP_CONTROL_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_DEPTH_CLIP_CONTROL_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PRIMITIVE_TOPOLOGY_LIST_RESTART_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_FORMAT_PROPERTIES_3 = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PRESENT_MODE_FIFO_LATEST_READY_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_SUBPASS_SHADING_PIPELINE_CREATE_INFO_HUAWEI = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SUBPASS_SHADING_FEATURES_HUAWEI = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SUBPASS_SHADING_PROPERTIES_HUAWEI = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_INVOCATION_MASK_FEATURES_HUAWEI = 0, VK_STRUCTURE_TYPE_PIPELINE_PROPERTIES_IDENTIFIER_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PIPELINE_PROPERTIES_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAME_BOUNDARY_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_FRAME_BOUNDARY_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MULTISAMPLED_RENDER_TO_SINGLE_SAMPLED_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_SUBPASS_RESOLVE_PERFORMANCE_QUERY_EXT = 0, VK_STRUCTURE_TYPE_MULTISAMPLED_RENDER_TO_SINGLE_SAMPLED_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTENDED_DYNAMIC_STATE_2_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COLOR_WRITE_ENABLE_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_COLOR_WRITE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PRIMITIVES_GENERATED_QUERY_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_TRACING_MAINTENANCE_1_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_UNTYPED_POINTERS_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_GLOBAL_PRIORITY_QUERY_FEATURES = 0, VK_STRUCTURE_TYPE_QUEUE_FAMILY_GLOBAL_PRIORITY_PROPERTIES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VIDEO_ENCODE_RGB_CONVERSION_FEATURES_VALVE = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_RGB_CONVERSION_CAPABILITIES_VALVE = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_PROFILE_RGB_CONVERSION_INFO_VALVE = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_SESSION_RGB_CONVERSION_CREATE_INFO_VALVE = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_VIEW_MIN_LOD_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_IMAGE_VIEW_MIN_LOD_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MULTI_DRAW_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MULTI_DRAW_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_2D_VIEW_OF_3D_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_TILE_IMAGE_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_TILE_IMAGE_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_MICROMAP_BUILD_INFO_EXT = 0, VK_STRUCTURE_TYPE_MICROMAP_VERSION_INFO_EXT = 0, VK_STRUCTURE_TYPE_COPY_MICROMAP_INFO_EXT = 0, VK_STRUCTURE_TYPE_COPY_MICROMAP_TO_MEMORY_INFO_EXT = 0, VK_STRUCTURE_TYPE_COPY_MEMORY_TO_MICROMAP_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_OPACITY_MICROMAP_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_OPACITY_MICROMAP_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_MICROMAP_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_MICROMAP_BUILD_SIZES_INFO_EXT = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_TRIANGLES_OPACITY_MICROMAP_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_CLUSTER_CULLING_SHADER_FEATURES_HUAWEI = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_CLUSTER_CULLING_SHADER_PROPERTIES_HUAWEI = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_CLUSTER_CULLING_SHADER_VRS_FEATURES_HUAWEI = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_BORDER_COLOR_SWIZZLE_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_SAMPLER_BORDER_COLOR_COMPONENT_MAPPING_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PAGEABLE_DEVICE_LOCAL_MEMORY_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_4_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_4_PROPERTIES = 0, VK_STRUCTURE_TYPE_DEVICE_BUFFER_MEMORY_REQUIREMENTS = 0, VK_STRUCTURE_TYPE_DEVICE_IMAGE_MEMORY_REQUIREMENTS = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_CORE_PROPERTIES_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_SUBGROUP_ROTATE_FEATURES = 0, VK_STRUCTURE_TYPE_DEVICE_QUEUE_SHADER_CORE_CONTROL_CREATE_INFO_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SCHEDULING_CONTROLS_FEATURES_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SCHEDULING_CONTROLS_PROPERTIES_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_SLICED_VIEW_OF_3D_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_IMAGE_VIEW_SLICED_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DESCRIPTOR_SET_HOST_MAPPING_FEATURES_VALVE = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_SET_BINDING_REFERENCE_VALVE = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_HOST_MAPPING_INFO_VALVE = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DEPTH_CLAMP_ZERO_ONE_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_NON_SEAMLESS_CUBE_MAP_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RENDER_PASS_STRIPED_FEATURES_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RENDER_PASS_STRIPED_PROPERTIES_ARM = 0, VK_STRUCTURE_TYPE_RENDER_PASS_STRIPE_BEGIN_INFO_ARM = 0, VK_STRUCTURE_TYPE_RENDER_PASS_STRIPE_INFO_ARM = 0, VK_STRUCTURE_TYPE_RENDER_PASS_STRIPE_SUBMIT_INFO_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_DENSITY_MAP_OFFSET_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_DENSITY_MAP_OFFSET_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_RENDER_PASS_FRAGMENT_DENSITY_MAP_OFFSET_END_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COPY_MEMORY_INDIRECT_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COPY_MEMORY_INDIRECT_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MEMORY_DECOMPRESSION_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MEMORY_DECOMPRESSION_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DEVICE_GENERATED_COMMANDS_COMPUTE_FEATURES_NV = 0, VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_INDIRECT_BUFFER_INFO_NV = 0, VK_STRUCTURE_TYPE_PIPELINE_INDIRECT_DEVICE_ADDRESS_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_TRACING_LINEAR_SWEPT_SPHERES_FEATURES_NV = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_GEOMETRY_LINEAR_SWEPT_SPHERES_DATA_NV = 0, VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_GEOMETRY_SPHERES_DATA_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_LINEAR_COLOR_ATTACHMENT_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_MAXIMAL_RECONVERGENCE_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_COMPRESSION_CONTROL_SWAPCHAIN_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_PROCESSING_FEATURES_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_PROCESSING_PROPERTIES_QCOM = 0, VK_STRUCTURE_TYPE_IMAGE_VIEW_SAMPLE_WEIGHT_CREATE_INFO_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_NESTED_COMMAND_BUFFER_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_NESTED_COMMAND_BUFFER_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_ACQUIRE_UNMODIFIED_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTENDED_DYNAMIC_STATE_3_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTENDED_DYNAMIC_STATE_3_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SUBPASS_MERGE_FEEDBACK_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_RENDER_PASS_CREATION_CONTROL_EXT = 0, VK_STRUCTURE_TYPE_RENDER_PASS_CREATION_FEEDBACK_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_RENDER_PASS_SUBPASS_FEEDBACK_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_TENSOR_CREATE_INFO_ARM = 0, VK_STRUCTURE_TYPE_TENSOR_VIEW_CREATE_INFO_ARM = 0, VK_STRUCTURE_TYPE_BIND_TENSOR_MEMORY_INFO_ARM = 0, VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET_TENSOR_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TENSOR_PROPERTIES_ARM = 0, VK_STRUCTURE_TYPE_TENSOR_FORMAT_PROPERTIES_ARM = 0, VK_STRUCTURE_TYPE_TENSOR_DESCRIPTION_ARM = 0, VK_STRUCTURE_TYPE_TENSOR_MEMORY_REQUIREMENTS_INFO_ARM = 0, VK_STRUCTURE_TYPE_TENSOR_MEMORY_BARRIER_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TENSOR_FEATURES_ARM = 0, VK_STRUCTURE_TYPE_DEVICE_TENSOR_MEMORY_REQUIREMENTS_ARM = 0, VK_STRUCTURE_TYPE_COPY_TENSOR_INFO_ARM = 0, VK_STRUCTURE_TYPE_TENSOR_COPY_ARM = 0, VK_STRUCTURE_TYPE_TENSOR_DEPENDENCY_INFO_ARM = 0, VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO_TENSOR_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_TENSOR_INFO_ARM = 0, VK_STRUCTURE_TYPE_EXTERNAL_TENSOR_PROPERTIES_ARM = 0, VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_TENSOR_CREATE_INFO_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DESCRIPTOR_BUFFER_TENSOR_FEATURES_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DESCRIPTOR_BUFFER_TENSOR_PROPERTIES_ARM = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_GET_TENSOR_INFO_ARM = 0, VK_STRUCTURE_TYPE_TENSOR_CAPTURE_DESCRIPTOR_DATA_INFO_ARM = 0, VK_STRUCTURE_TYPE_TENSOR_VIEW_CAPTURE_DESCRIPTOR_DATA_INFO_ARM = 0, VK_STRUCTURE_TYPE_FRAME_BOUNDARY_TENSORS_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_MODULE_IDENTIFIER_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_MODULE_IDENTIFIER_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_MODULE_IDENTIFIER_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_SHADER_MODULE_IDENTIFIER_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_OPTICAL_FLOW_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_OPTICAL_FLOW_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_OPTICAL_FLOW_IMAGE_FORMAT_INFO_NV = 0, VK_STRUCTURE_TYPE_OPTICAL_FLOW_IMAGE_FORMAT_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_OPTICAL_FLOW_SESSION_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_OPTICAL_FLOW_EXECUTE_INFO_NV = 0, VK_STRUCTURE_TYPE_OPTICAL_FLOW_SESSION_CREATE_PRIVATE_DATA_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_LEGACY_DITHERING_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PIPELINE_PROTECTED_ACCESS_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_5_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_5_PROPERTIES = 0, VK_STRUCTURE_TYPE_RENDERING_AREA_INFO = 0, VK_STRUCTURE_TYPE_DEVICE_IMAGE_SUBRESOURCE_INFO = 0, VK_STRUCTURE_TYPE_PIPELINE_CREATE_FLAGS_2_CREATE_INFO = 0, VK_STRUCTURE_TYPE_BUFFER_USAGE_FLAGS_2_CREATE_INFO = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ANTI_LAG_FEATURES_AMD = 0, VK_STRUCTURE_TYPE_ANTI_LAG_DATA_AMD = 0, VK_STRUCTURE_TYPE_ANTI_LAG_PRESENTATION_INFO_AMD = 0, VK_STRUCTURE_TYPE_SURFACE_CAPABILITIES_PRESENT_ID_2_KHR = 0, VK_STRUCTURE_TYPE_PRESENT_ID_2_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PRESENT_ID_2_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_SURFACE_CAPABILITIES_PRESENT_WAIT_2_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PRESENT_WAIT_2_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PRESENT_WAIT_2_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_TRACING_POSITION_FETCH_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_OBJECT_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_OBJECT_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_SHADER_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PIPELINE_BINARY_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_BINARY_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_BINARY_INFO_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_BINARY_KEY_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PIPELINE_BINARY_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_RELEASE_CAPTURED_PIPELINE_DATA_INFO_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_BINARY_DATA_INFO_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_DEVICE_PIPELINE_BINARY_INTERNAL_CACHE_CONTROL_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_BINARY_HANDLES_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TILE_PROPERTIES_FEATURES_QCOM = 0, VK_STRUCTURE_TYPE_TILE_PROPERTIES_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MULTIVIEW_PER_VIEW_VIEWPORTS_FEATURES_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_TRACING_INVOCATION_REORDER_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_TRACING_INVOCATION_REORDER_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COOPERATIVE_VECTOR_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COOPERATIVE_VECTOR_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_COOPERATIVE_VECTOR_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_CONVERT_COOPERATIVE_VECTOR_MATRIX_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTENDED_SPARSE_ADDRESS_SPACE_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTENDED_SPARSE_ADDRESS_SPACE_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_LEGACY_VERTEX_ATTRIBUTES_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_LEGACY_VERTEX_ATTRIBUTES_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_LAYER_SETTINGS_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_CORE_BUILTINS_FEATURES_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_CORE_BUILTINS_PROPERTIES_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PIPELINE_LIBRARY_GROUP_HANDLES_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DYNAMIC_RENDERING_UNUSED_ATTACHMENTS_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_LATENCY_SLEEP_MODE_INFO_NV = 0, VK_STRUCTURE_TYPE_LATENCY_SLEEP_INFO_NV = 0, VK_STRUCTURE_TYPE_SET_LATENCY_MARKER_INFO_NV = 0, VK_STRUCTURE_TYPE_GET_LATENCY_MARKER_INFO_NV = 0, VK_STRUCTURE_TYPE_LATENCY_TIMINGS_FRAME_REPORT_NV = 0, VK_STRUCTURE_TYPE_LATENCY_SUBMISSION_PRESENT_ID_NV = 0, VK_STRUCTURE_TYPE_OUT_OF_BAND_QUEUE_TYPE_INFO_NV = 0, VK_STRUCTURE_TYPE_SWAPCHAIN_LATENCY_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_LATENCY_SURFACE_CAPABILITIES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COOPERATIVE_MATRIX_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_COOPERATIVE_MATRIX_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COOPERATIVE_MATRIX_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_DATA_GRAPH_PIPELINE_CREATE_INFO_ARM = 0, VK_STRUCTURE_TYPE_DATA_GRAPH_PIPELINE_SESSION_CREATE_INFO_ARM = 0, VK_STRUCTURE_TYPE_DATA_GRAPH_PIPELINE_RESOURCE_INFO_ARM = 0, VK_STRUCTURE_TYPE_DATA_GRAPH_PIPELINE_CONSTANT_ARM = 0, VK_STRUCTURE_TYPE_DATA_GRAPH_PIPELINE_SESSION_MEMORY_REQUIREMENTS_INFO_ARM = 0, VK_STRUCTURE_TYPE_BIND_DATA_GRAPH_PIPELINE_SESSION_MEMORY_INFO_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DATA_GRAPH_FEATURES_ARM = 0, VK_STRUCTURE_TYPE_DATA_GRAPH_PIPELINE_SHADER_MODULE_CREATE_INFO_ARM = 0, VK_STRUCTURE_TYPE_DATA_GRAPH_PIPELINE_PROPERTY_QUERY_RESULT_ARM = 0, VK_STRUCTURE_TYPE_DATA_GRAPH_PIPELINE_INFO_ARM = 0, VK_STRUCTURE_TYPE_DATA_GRAPH_PIPELINE_COMPILER_CONTROL_CREATE_INFO_ARM = 0, VK_STRUCTURE_TYPE_DATA_GRAPH_PIPELINE_SESSION_BIND_POINT_REQUIREMENTS_INFO_ARM = 0, VK_STRUCTURE_TYPE_DATA_GRAPH_PIPELINE_SESSION_BIND_POINT_REQUIREMENT_ARM = 0, VK_STRUCTURE_TYPE_DATA_GRAPH_PIPELINE_IDENTIFIER_CREATE_INFO_ARM = 0, VK_STRUCTURE_TYPE_DATA_GRAPH_PIPELINE_DISPATCH_INFO_ARM = 0, VK_STRUCTURE_TYPE_DATA_GRAPH_PIPELINE_CONSTANT_TENSOR_SEMI_STRUCTURED_SPARSITY_INFO_ARM = 0, VK_STRUCTURE_TYPE_DATA_GRAPH_PROCESSING_ENGINE_CREATE_INFO_ARM = 0, VK_STRUCTURE_TYPE_QUEUE_FAMILY_DATA_GRAPH_PROCESSING_ENGINE_PROPERTIES_ARM = 0, VK_STRUCTURE_TYPE_QUEUE_FAMILY_DATA_GRAPH_PROPERTIES_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_QUEUE_FAMILY_DATA_GRAPH_PROCESSING_ENGINE_INFO_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MULTIVIEW_PER_VIEW_RENDER_AREAS_FEATURES_QCOM = 0, VK_STRUCTURE_TYPE_MULTIVIEW_PER_VIEW_RENDER_AREAS_RENDER_PASS_BEGIN_INFO_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COMPUTE_SHADER_DERIVATIVES_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_AV1_CAPABILITIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_AV1_PICTURE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_AV1_PROFILE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_AV1_SESSION_PARAMETERS_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_AV1_DPB_SLOT_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_AV1_CAPABILITIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_AV1_SESSION_PARAMETERS_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_AV1_PICTURE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_AV1_DPB_SLOT_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VIDEO_ENCODE_AV1_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_AV1_PROFILE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_AV1_RATE_CONTROL_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_AV1_RATE_CONTROL_LAYER_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_AV1_QUALITY_LEVEL_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_AV1_SESSION_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_AV1_GOP_REMAINING_FRAME_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VIDEO_DECODE_VP9_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_VP9_CAPABILITIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_VP9_PICTURE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_DECODE_VP9_PROFILE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VIDEO_MAINTENANCE_1_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_INLINE_QUERY_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PER_STAGE_DESCRIPTOR_SET_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_PROCESSING_2_FEATURES_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_PROCESSING_2_PROPERTIES_QCOM = 0, VK_STRUCTURE_TYPE_SAMPLER_BLOCK_MATCH_WINDOW_CREATE_INFO_QCOM = 0, VK_STRUCTURE_TYPE_SAMPLER_CUBIC_WEIGHTS_CREATE_INFO_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_CUBIC_WEIGHTS_FEATURES_QCOM = 0, VK_STRUCTURE_TYPE_BLIT_IMAGE_CUBIC_WEIGHTS_INFO_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_YCBCR_DEGAMMA_FEATURES_QCOM = 0, VK_STRUCTURE_TYPE_SAMPLER_YCBCR_CONVERSION_YCBCR_DEGAMMA_CREATE_INFO_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_CUBIC_CLAMP_FEATURES_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ATTACHMENT_FEEDBACK_LOOP_DYNAMIC_STATE_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VERTEX_ATTRIBUTE_DIVISOR_PROPERTIES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_UNIFIED_IMAGE_LAYOUTS_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_ATTACHMENT_FEEDBACK_LOOP_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_FLOAT_CONTROLS_2_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_LAYERED_DRIVER_PROPERTIES_MSFT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_EXPECT_ASSUME_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_6_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_6_PROPERTIES = 0, VK_STRUCTURE_TYPE_BIND_MEMORY_STATUS = 0, VK_STRUCTURE_TYPE_BIND_DESCRIPTOR_SETS_INFO = 0, VK_STRUCTURE_TYPE_PUSH_CONSTANTS_INFO = 0, VK_STRUCTURE_TYPE_PUSH_DESCRIPTOR_SET_INFO = 0, VK_STRUCTURE_TYPE_PUSH_DESCRIPTOR_SET_WITH_TEMPLATE_INFO = 0, VK_STRUCTURE_TYPE_SET_DESCRIPTOR_BUFFER_OFFSETS_INFO_EXT = 0, VK_STRUCTURE_TYPE_BIND_DESCRIPTOR_BUFFER_EMBEDDED_SAMPLERS_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DESCRIPTOR_POOL_OVERALLOCATION_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TILE_MEMORY_HEAP_FEATURES_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TILE_MEMORY_HEAP_PROPERTIES_QCOM = 0, VK_STRUCTURE_TYPE_TILE_MEMORY_REQUIREMENTS_QCOM = 0, VK_STRUCTURE_TYPE_TILE_MEMORY_BIND_INFO_QCOM = 0, VK_STRUCTURE_TYPE_TILE_MEMORY_SIZE_INFO_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COPY_MEMORY_INDIRECT_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_COPY_MEMORY_INDIRECT_INFO_KHR = 0, VK_STRUCTURE_TYPE_COPY_MEMORY_TO_IMAGE_INDIRECT_INFO_KHR = 0, VK_STRUCTURE_TYPE_DECOMPRESS_MEMORY_INFO_EXT = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_INTRA_REFRESH_CAPABILITIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_SESSION_INTRA_REFRESH_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_INTRA_REFRESH_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_REFERENCE_INTRA_REFRESH_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VIDEO_ENCODE_INTRA_REFRESH_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_QUANTIZATION_MAP_CAPABILITIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_FORMAT_QUANTIZATION_MAP_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_QUANTIZATION_MAP_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_QUANTIZATION_MAP_CAPABILITIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_H265_QUANTIZATION_MAP_CAPABILITIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_QUANTIZATION_MAP_SESSION_PARAMETERS_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_FORMAT_H265_QUANTIZATION_MAP_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_ENCODE_AV1_QUANTIZATION_MAP_CAPABILITIES_KHR = 0, VK_STRUCTURE_TYPE_VIDEO_FORMAT_AV1_QUANTIZATION_MAP_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VIDEO_ENCODE_QUANTIZATION_MAP_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAW_ACCESS_CHAINS_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_RELAXED_EXTENDED_INSTRUCTION_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COMMAND_BUFFER_INHERITANCE_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_ATOMIC_FLOAT16_VECTOR_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_REPLICATED_COMPOSITES_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_FLOAT8_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_TRACING_VALIDATION_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_CLUSTER_ACCELERATION_STRUCTURE_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_CLUSTER_ACCELERATION_STRUCTURE_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_CLUSTER_ACCELERATION_STRUCTURE_CLUSTERS_BOTTOM_LEVEL_INPUT_NV = 0, VK_STRUCTURE_TYPE_CLUSTER_ACCELERATION_STRUCTURE_TRIANGLE_CLUSTER_INPUT_NV = 0, VK_STRUCTURE_TYPE_CLUSTER_ACCELERATION_STRUCTURE_MOVE_OBJECTS_INPUT_NV = 0, VK_STRUCTURE_TYPE_CLUSTER_ACCELERATION_STRUCTURE_INPUT_INFO_NV = 0, VK_STRUCTURE_TYPE_CLUSTER_ACCELERATION_STRUCTURE_COMMANDS_INFO_NV = 0, VK_STRUCTURE_TYPE_RAY_TRACING_PIPELINE_CLUSTER_ACCELERATION_STRUCTURE_CREATE_INFO_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PARTITIONED_ACCELERATION_STRUCTURE_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PARTITIONED_ACCELERATION_STRUCTURE_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET_PARTITIONED_ACCELERATION_STRUCTURE_NV = 0, VK_STRUCTURE_TYPE_PARTITIONED_ACCELERATION_STRUCTURE_INSTANCES_INPUT_NV = 0, VK_STRUCTURE_TYPE_BUILD_PARTITIONED_ACCELERATION_STRUCTURE_INFO_NV = 0, VK_STRUCTURE_TYPE_PARTITIONED_ACCELERATION_STRUCTURE_FLAGS_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DEVICE_GENERATED_COMMANDS_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DEVICE_GENERATED_COMMANDS_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_GENERATED_COMMANDS_MEMORY_REQUIREMENTS_INFO_EXT = 0, VK_STRUCTURE_TYPE_INDIRECT_EXECUTION_SET_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_GENERATED_COMMANDS_INFO_EXT = 0, VK_STRUCTURE_TYPE_INDIRECT_COMMANDS_LAYOUT_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_INDIRECT_COMMANDS_LAYOUT_TOKEN_EXT = 0, VK_STRUCTURE_TYPE_WRITE_INDIRECT_EXECUTION_SET_PIPELINE_EXT = 0, VK_STRUCTURE_TYPE_WRITE_INDIRECT_EXECUTION_SET_SHADER_EXT = 0, VK_STRUCTURE_TYPE_INDIRECT_EXECUTION_SET_PIPELINE_INFO_EXT = 0, VK_STRUCTURE_TYPE_INDIRECT_EXECUTION_SET_SHADER_INFO_EXT = 0, VK_STRUCTURE_TYPE_INDIRECT_EXECUTION_SET_SHADER_LAYOUT_INFO_EXT = 0, VK_STRUCTURE_TYPE_GENERATED_COMMANDS_PIPELINE_INFO_EXT = 0, VK_STRUCTURE_TYPE_GENERATED_COMMANDS_SHADER_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_8_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_MEMORY_BARRIER_ACCESS_FLAGS_3_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_ALIGNMENT_CONTROL_FEATURES_MESA = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_ALIGNMENT_CONTROL_PROPERTIES_MESA = 0, VK_STRUCTURE_TYPE_IMAGE_ALIGNMENT_CONTROL_CREATE_INFO_MESA = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_FMA_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_TRACING_INVOCATION_REORDER_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_TRACING_INVOCATION_REORDER_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DEPTH_CLAMP_CONTROL_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_DEPTH_CLAMP_CONTROL_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_9_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_9_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_QUEUE_FAMILY_OWNERSHIP_TRANSFER_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_HDR_VIVID_FEATURES_HUAWEI = 0, VK_STRUCTURE_TYPE_HDR_VIVID_DYNAMIC_METADATA_HUAWEI = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COOPERATIVE_MATRIX_2_FEATURES_NV = 0, VK_STRUCTURE_TYPE_COOPERATIVE_MATRIX_FLEXIBLE_DIMENSIONS_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COOPERATIVE_MATRIX_2_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PIPELINE_OPACITY_MICROMAP_FEATURES_ARM = 0, VK_STRUCTURE_TYPE_IMPORT_MEMORY_METAL_HANDLE_INFO_EXT = 0, VK_STRUCTURE_TYPE_MEMORY_METAL_HANDLE_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_MEMORY_GET_METAL_HANDLE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PERFORMANCE_COUNTERS_BY_REGION_FEATURES_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PERFORMANCE_COUNTERS_BY_REGION_PROPERTIES_ARM = 0, VK_STRUCTURE_TYPE_PERFORMANCE_COUNTER_ARM = 0, VK_STRUCTURE_TYPE_PERFORMANCE_COUNTER_DESCRIPTION_ARM = 0, VK_STRUCTURE_TYPE_RENDER_PASS_PERFORMANCE_COUNTERS_BY_REGION_BEGIN_INFO_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VERTEX_ATTRIBUTE_ROBUSTNESS_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FORMAT_PACK_FEATURES_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_DENSITY_MAP_LAYERED_FEATURES_VALVE = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_DENSITY_MAP_LAYERED_PROPERTIES_VALVE = 0, VK_STRUCTURE_TYPE_PIPELINE_FRAGMENT_DENSITY_MAP_LAYERED_CREATE_INFO_VALVE = 0, VK_STRUCTURE_TYPE_RENDERING_END_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ZERO_INITIALIZE_DEVICE_MEMORY_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_64_BIT_INDEXING_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_CUSTOM_RESOLVE_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_BEGIN_CUSTOM_RESOLVE_INFO_EXT = 0, VK_STRUCTURE_TYPE_CUSTOM_RESOLVE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DATA_GRAPH_MODEL_FEATURES_QCOM = 0, VK_STRUCTURE_TYPE_DATA_GRAPH_PIPELINE_BUILTIN_MODEL_CREATE_INFO_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_10_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_10_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_FLAGS_INFO_KHR = 0, VK_STRUCTURE_TYPE_RESOLVE_IMAGE_MODE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PIPELINE_CACHE_INCREMENTAL_MODE_FEATURES_SEC = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_UNIFORM_BUFFER_UNSIZED_ARRAY_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_MAX_ENUM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VARIABLE_POINTER_FEATURES = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_DRAW_PARAMETER_FEATURES = 0, VK_STRUCTURE_TYPE_DEBUG_REPORT_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_RENDERING_INFO_KHR = 0, VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_INFO_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_RENDERING_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DYNAMIC_RENDERING_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_COMMAND_BUFFER_INHERITANCE_RENDERING_INFO_KHR = 0, VK_STRUCTURE_TYPE_RENDER_PASS_MULTIVIEW_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MULTIVIEW_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MULTIVIEW_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2_KHR = 0, VK_STRUCTURE_TYPE_FORMAT_PROPERTIES_2_KHR = 0, VK_STRUCTURE_TYPE_IMAGE_FORMAT_PROPERTIES_2_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_FORMAT_INFO_2_KHR = 0, VK_STRUCTURE_TYPE_QUEUE_FAMILY_PROPERTIES_2_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MEMORY_PROPERTIES_2_KHR = 0, VK_STRUCTURE_TYPE_SPARSE_IMAGE_FORMAT_PROPERTIES_2_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SPARSE_IMAGE_FORMAT_INFO_2_KHR = 0, VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_FLAGS_INFO_KHR = 0, VK_STRUCTURE_TYPE_DEVICE_GROUP_RENDER_PASS_BEGIN_INFO_KHR = 0, VK_STRUCTURE_TYPE_DEVICE_GROUP_COMMAND_BUFFER_BEGIN_INFO_KHR = 0, VK_STRUCTURE_TYPE_DEVICE_GROUP_SUBMIT_INFO_KHR = 0, VK_STRUCTURE_TYPE_DEVICE_GROUP_BIND_SPARSE_INFO_KHR = 0, VK_STRUCTURE_TYPE_BIND_BUFFER_MEMORY_DEVICE_GROUP_INFO_KHR = 0, VK_STRUCTURE_TYPE_BIND_IMAGE_MEMORY_DEVICE_GROUP_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TEXTURE_COMPRESSION_ASTC_HDR_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_ROBUSTNESS_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PIPELINE_ROBUSTNESS_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PIPELINE_ROBUSTNESS_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_GROUP_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_DEVICE_GROUP_DEVICE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_IMAGE_FORMAT_INFO_KHR = 0, VK_STRUCTURE_TYPE_EXTERNAL_IMAGE_FORMAT_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_BUFFER_INFO_KHR = 0, VK_STRUCTURE_TYPE_EXTERNAL_BUFFER_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ID_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_BUFFER_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_EXPORT_MEMORY_ALLOCATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_SEMAPHORE_INFO_KHR = 0, VK_STRUCTURE_TYPE_EXTERNAL_SEMAPHORE_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_EXPORT_SEMAPHORE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PUSH_DESCRIPTOR_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_FLOAT16_INT8_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FLOAT16_INT8_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_16BIT_STORAGE_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_UPDATE_TEMPLATE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGELESS_FRAMEBUFFER_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_FRAMEBUFFER_ATTACHMENTS_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_FRAMEBUFFER_ATTACHMENT_IMAGE_INFO_KHR = 0, VK_STRUCTURE_TYPE_RENDER_PASS_ATTACHMENT_BEGIN_INFO_KHR = 0, VK_STRUCTURE_TYPE_ATTACHMENT_DESCRIPTION_2_KHR = 0, VK_STRUCTURE_TYPE_ATTACHMENT_REFERENCE_2_KHR = 0, VK_STRUCTURE_TYPE_SUBPASS_DESCRIPTION_2_KHR = 0, VK_STRUCTURE_TYPE_SUBPASS_DEPENDENCY_2_KHR = 0, VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO_2_KHR = 0, VK_STRUCTURE_TYPE_SUBPASS_BEGIN_INFO_KHR = 0, VK_STRUCTURE_TYPE_SUBPASS_END_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_FENCE_INFO_KHR = 0, VK_STRUCTURE_TYPE_EXTERNAL_FENCE_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_EXPORT_FENCE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_POINT_CLIPPING_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_RENDER_PASS_INPUT_ATTACHMENT_ASPECT_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_IMAGE_VIEW_USAGE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_TESSELLATION_DOMAIN_ORIGIN_STATE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VARIABLE_POINTERS_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VARIABLE_POINTER_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_MEMORY_DEDICATED_REQUIREMENTS_KHR = 0, VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SAMPLER_FILTER_MINMAX_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_SAMPLER_REDUCTION_MODE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_INLINE_UNIFORM_BLOCK_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_INLINE_UNIFORM_BLOCK_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET_INLINE_UNIFORM_BLOCK_EXT = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_INLINE_UNIFORM_BLOCK_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_BUFFER_MEMORY_REQUIREMENTS_INFO_2_KHR = 0, VK_STRUCTURE_TYPE_IMAGE_MEMORY_REQUIREMENTS_INFO_2_KHR = 0, VK_STRUCTURE_TYPE_IMAGE_SPARSE_MEMORY_REQUIREMENTS_INFO_2_KHR = 0, VK_STRUCTURE_TYPE_MEMORY_REQUIREMENTS_2_KHR = 0, VK_STRUCTURE_TYPE_SPARSE_IMAGE_MEMORY_REQUIREMENTS_2_KHR = 0, VK_STRUCTURE_TYPE_IMAGE_FORMAT_LIST_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_ATTACHMENT_SAMPLE_COUNT_INFO_NV = 0, VK_STRUCTURE_TYPE_SAMPLER_YCBCR_CONVERSION_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_SAMPLER_YCBCR_CONVERSION_INFO_KHR = 0, VK_STRUCTURE_TYPE_BIND_IMAGE_PLANE_MEMORY_INFO_KHR = 0, VK_STRUCTURE_TYPE_IMAGE_PLANE_MEMORY_REQUIREMENTS_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SAMPLER_YCBCR_CONVERSION_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_SAMPLER_YCBCR_CONVERSION_IMAGE_FORMAT_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_BIND_BUFFER_MEMORY_INFO_KHR = 0, VK_STRUCTURE_TYPE_BIND_IMAGE_MEMORY_INFO_KHR = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_BINDING_FLAGS_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DESCRIPTOR_INDEXING_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DESCRIPTOR_INDEXING_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_SET_VARIABLE_DESCRIPTOR_COUNT_ALLOCATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_SET_VARIABLE_DESCRIPTOR_COUNT_LAYOUT_SUPPORT_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_3_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_SUPPORT_KHR = 0, VK_STRUCTURE_TYPE_DEVICE_QUEUE_GLOBAL_PRIORITY_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_SUBGROUP_EXTENDED_TYPES_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_8BIT_STORAGE_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_ATOMIC_INT64_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_CALIBRATED_TIMESTAMP_INFO_EXT = 0, VK_STRUCTURE_TYPE_DEVICE_QUEUE_GLOBAL_PRIORITY_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_GLOBAL_PRIORITY_QUERY_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_QUEUE_FAMILY_GLOBAL_PRIORITY_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_DIVISOR_STATE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VERTEX_ATTRIBUTE_DIVISOR_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_CREATION_FEEDBACK_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DRIVER_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FLOAT_CONTROLS_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DEPTH_STENCIL_RESOLVE_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_SUBPASS_DESCRIPTION_DEPTH_STENCIL_RESOLVE_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COMPUTE_SHADER_DERIVATIVES_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_SHADER_BARYCENTRIC_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TIMELINE_SEMAPHORE_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TIMELINE_SEMAPHORE_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_SEMAPHORE_TYPE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_TIMELINE_SEMAPHORE_SUBMIT_INFO_KHR = 0, VK_STRUCTURE_TYPE_SEMAPHORE_WAIT_INFO_KHR = 0, VK_STRUCTURE_TYPE_SEMAPHORE_SIGNAL_INFO_KHR = 0, VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO_INTEL = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_MEMORY_MODEL_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_TERMINATE_INVOCATION_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SCALAR_BLOCK_LAYOUT_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SUBGROUP_SIZE_CONTROL_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_REQUIRED_SUBGROUP_SIZE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SUBGROUP_SIZE_CONTROL_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DYNAMIC_RENDERING_LOCAL_READ_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_LOCATION_INFO_KHR = 0, VK_STRUCTURE_TYPE_RENDERING_INPUT_ATTACHMENT_INDEX_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SEPARATE_DEPTH_STENCIL_LAYOUTS_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_ATTACHMENT_REFERENCE_STENCIL_LAYOUT_KHR = 0, VK_STRUCTURE_TYPE_ATTACHMENT_DESCRIPTION_STENCIL_LAYOUT_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_BUFFER_ADDRESS_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_BUFFER_DEVICE_ADDRESS_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TOOL_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_IMAGE_STENCIL_USAGE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_UNIFORM_BUFFER_STANDARD_LAYOUT_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_BUFFER_DEVICE_ADDRESS_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_BUFFER_DEVICE_ADDRESS_INFO_KHR = 0, VK_STRUCTURE_TYPE_BUFFER_OPAQUE_CAPTURE_ADDRESS_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_MEMORY_OPAQUE_CAPTURE_ADDRESS_ALLOCATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_DEVICE_MEMORY_OPAQUE_CAPTURE_ADDRESS_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_LINE_RASTERIZATION_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_LINE_STATE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_LINE_RASTERIZATION_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_HOST_QUERY_RESET_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_INDEX_TYPE_UINT8_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_HOST_IMAGE_COPY_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_HOST_IMAGE_COPY_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_MEMORY_TO_IMAGE_COPY_EXT = 0, VK_STRUCTURE_TYPE_IMAGE_TO_MEMORY_COPY_EXT = 0, VK_STRUCTURE_TYPE_COPY_IMAGE_TO_MEMORY_INFO_EXT = 0, VK_STRUCTURE_TYPE_COPY_MEMORY_TO_IMAGE_INFO_EXT = 0, VK_STRUCTURE_TYPE_HOST_IMAGE_LAYOUT_TRANSITION_INFO_EXT = 0, VK_STRUCTURE_TYPE_COPY_IMAGE_TO_IMAGE_INFO_EXT = 0, VK_STRUCTURE_TYPE_SUBRESOURCE_HOST_MEMCPY_SIZE_EXT = 0, VK_STRUCTURE_TYPE_HOST_IMAGE_COPY_DEVICE_PERFORMANCE_QUERY_EXT = 0, VK_STRUCTURE_TYPE_MEMORY_MAP_INFO_KHR = 0, VK_STRUCTURE_TYPE_MEMORY_UNMAP_INFO_KHR = 0, VK_STRUCTURE_TYPE_SURFACE_PRESENT_MODE_EXT = 0, VK_STRUCTURE_TYPE_SURFACE_PRESENT_SCALING_CAPABILITIES_EXT = 0, VK_STRUCTURE_TYPE_SURFACE_PRESENT_MODE_COMPATIBILITY_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SWAPCHAIN_MAINTENANCE_1_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_SWAPCHAIN_PRESENT_FENCE_INFO_EXT = 0, VK_STRUCTURE_TYPE_SWAPCHAIN_PRESENT_MODES_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_SWAPCHAIN_PRESENT_MODE_INFO_EXT = 0, VK_STRUCTURE_TYPE_SWAPCHAIN_PRESENT_SCALING_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_RELEASE_SWAPCHAIN_IMAGES_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_DEMOTE_TO_HELPER_INVOCATION_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_INTEGER_DOT_PRODUCT_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_INTEGER_DOT_PRODUCT_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TEXEL_BUFFER_ALIGNMENT_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ROBUSTNESS_2_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ROBUSTNESS_2_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PRIVATE_DATA_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_DEVICE_PRIVATE_DATA_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PRIVATE_DATA_SLOT_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PIPELINE_CREATION_CACHE_CONTROL_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_MEMORY_BARRIER_2_KHR = 0, VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER_2_KHR = 0, VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2_KHR = 0, VK_STRUCTURE_TYPE_DEPENDENCY_INFO_KHR = 0, VK_STRUCTURE_TYPE_SUBMIT_INFO_2_KHR = 0, VK_STRUCTURE_TYPE_SEMAPHORE_SUBMIT_INFO_KHR = 0, VK_STRUCTURE_TYPE_COMMAND_BUFFER_SUBMIT_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SYNCHRONIZATION_2_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ZERO_INITIALIZE_WORKGROUP_MEMORY_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_ROBUSTNESS_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_COPY_BUFFER_INFO_2_KHR = 0, VK_STRUCTURE_TYPE_COPY_IMAGE_INFO_2_KHR = 0, VK_STRUCTURE_TYPE_COPY_BUFFER_TO_IMAGE_INFO_2_KHR = 0, VK_STRUCTURE_TYPE_COPY_IMAGE_TO_BUFFER_INFO_2_KHR = 0, VK_STRUCTURE_TYPE_BLIT_IMAGE_INFO_2_KHR = 0, VK_STRUCTURE_TYPE_RESOLVE_IMAGE_INFO_2_KHR = 0, VK_STRUCTURE_TYPE_BUFFER_COPY_2_KHR = 0, VK_STRUCTURE_TYPE_IMAGE_COPY_2_KHR = 0, VK_STRUCTURE_TYPE_IMAGE_BLIT_2_KHR = 0, VK_STRUCTURE_TYPE_BUFFER_IMAGE_COPY_2_KHR = 0, VK_STRUCTURE_TYPE_IMAGE_RESOLVE_2_KHR = 0, VK_STRUCTURE_TYPE_SUBRESOURCE_LAYOUT_2_EXT = 0, VK_STRUCTURE_TYPE_IMAGE_SUBRESOURCE_2_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RASTERIZATION_ORDER_ATTACHMENT_ACCESS_FEATURES_ARM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MUTABLE_DESCRIPTOR_TYPE_FEATURES_VALVE = 0, VK_STRUCTURE_TYPE_MUTABLE_DESCRIPTOR_TYPE_CREATE_INFO_VALVE = 0, VK_STRUCTURE_TYPE_FORMAT_PROPERTIES_3_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PRESENT_MODE_FIFO_LATEST_READY_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PIPELINE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_GLOBAL_PRIORITY_QUERY_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_QUEUE_FAMILY_GLOBAL_PRIORITY_PROPERTIES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_4_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_4_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_DEVICE_BUFFER_MEMORY_REQUIREMENTS_KHR = 0, VK_STRUCTURE_TYPE_DEVICE_IMAGE_MEMORY_REQUIREMENTS_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_SUBGROUP_ROTATE_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DEPTH_CLAMP_ZERO_ONE_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_DENSITY_MAP_OFFSET_FEATURES_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_DENSITY_MAP_OFFSET_PROPERTIES_QCOM = 0, VK_STRUCTURE_TYPE_SUBPASS_FRAGMENT_DENSITY_MAP_OFFSET_END_INFO_QCOM = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COPY_MEMORY_INDIRECT_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MEMORY_DECOMPRESSION_FEATURES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MEMORY_DECOMPRESSION_PROPERTIES_NV = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PIPELINE_PROTECTED_ACCESS_FEATURES_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_5_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_5_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_RENDERING_AREA_INFO_KHR = 0, VK_STRUCTURE_TYPE_DEVICE_IMAGE_SUBRESOURCE_INFO_KHR = 0, VK_STRUCTURE_TYPE_SUBRESOURCE_LAYOUT_2_KHR = 0, VK_STRUCTURE_TYPE_IMAGE_SUBRESOURCE_2_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_CREATE_FLAGS_2_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_BUFFER_USAGE_FLAGS_2_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_SHADER_REQUIRED_SUBGROUP_SIZE_CREATE_INFO_EXT = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VERTEX_ATTRIBUTE_DIVISOR_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_DIVISOR_STATE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VERTEX_ATTRIBUTE_DIVISOR_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_FLOAT_CONTROLS_2_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_INDEX_TYPE_UINT8_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_LINE_RASTERIZATION_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_LINE_STATE_CREATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_LINE_RASTERIZATION_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_EXPECT_ASSUME_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_6_FEATURES_KHR = 0, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_6_PROPERTIES_KHR = 0, VK_STRUCTURE_TYPE_BIND_MEMORY_STATUS_KHR = 0, VK_STRUCTURE_TYPE_BIND_DESCRIPTOR_SETS_INFO_KHR = 0, VK_STRUCTURE_TYPE_PUSH_CONSTANTS_INFO_KHR = 0, VK_STRUCTURE_TYPE_PUSH_DESCRIPTOR_SET_INFO_KHR = 0, VK_STRUCTURE_TYPE_PUSH_DESCRIPTOR_SET_WITH_TEMPLATE_INFO_KHR = 0, VK_STRUCTURE_TYPE_RENDERING_END_INFO_EXT = 0 };
enum VkSubpassContents { VK_SUBPASS_CONTENTS_INLINE = 0, VK_SUBPASS_CONTENTS_SECONDARY_COMMAND_BUFFERS = 1, VK_SUBPASS_CONTENTS_INLINE_AND_SECONDARY_COMMAND_BUFFERS_KHR = 0, VK_SUBPASS_CONTENTS_MAX_ENUM = 0, VK_SUBPASS_CONTENTS_INLINE_AND_SECONDARY_COMMAND_BUFFERS_EXT = 0 };
enum VkSurfaceTransformFlagBitsKHR { VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR = 1, VK_SURFACE_TRANSFORM_ROTATE_90_BIT_KHR = 2, VK_SURFACE_TRANSFORM_ROTATE_180_BIT_KHR = 4, VK_SURFACE_TRANSFORM_ROTATE_270_BIT_KHR = 8, VK_SURFACE_TRANSFORM_HORIZONTAL_MIRROR_BIT_KHR = 16, VK_SURFACE_TRANSFORM_HORIZONTAL_MIRROR_ROTATE_90_BIT_KHR = 32, VK_SURFACE_TRANSFORM_HORIZONTAL_MIRROR_ROTATE_180_BIT_KHR = 64, VK_SURFACE_TRANSFORM_HORIZONTAL_MIRROR_ROTATE_270_BIT_KHR = 128, VK_SURFACE_TRANSFORM_INHERIT_BIT_KHR = 256, VK_SURFACE_TRANSFORM_FLAG_BITS_KHR_MAX_ENUM = 0 };
enum VkSystemAllocationScope { VK_SYSTEM_ALLOCATION_SCOPE_COMMAND = 0, VK_SYSTEM_ALLOCATION_SCOPE_OBJECT = 1, VK_SYSTEM_ALLOCATION_SCOPE_CACHE = 2, VK_SYSTEM_ALLOCATION_SCOPE_DEVICE = 3, VK_SYSTEM_ALLOCATION_SCOPE_INSTANCE = 4, VK_SYSTEM_ALLOCATION_SCOPE_MAX_ENUM = 0 };
enum VkVertexInputRate { VK_VERTEX_INPUT_RATE_VERTEX = 0, VK_VERTEX_INPUT_RATE_INSTANCE = 1, VK_VERTEX_INPUT_RATE_MAX_ENUM = 0 };
enum VkVideoCodecOperationFlagBitsKHR { VK_VIDEO_CODEC_OPERATION_NONE_KHR = 0, VK_VIDEO_CODEC_OPERATION_DECODE_H264_BIT_KHR = 1, VK_VIDEO_CODEC_OPERATION_DECODE_AV1_BIT_KHR = 4, VK_VIDEO_CODEC_OPERATION_DECODE_VP9_BIT_KHR = 8, VK_VIDEO_CODEC_OPERATION_ENCODE_H264_BIT_KHR = 0, VK_VIDEO_CODEC_OPERATION_ENCODE_AV1_BIT_KHR = 0, VK_VIDEO_CODEC_OPERATION_FLAG_BITS_KHR_MAX_ENUM = 0 };
enum wined3d_vk_extension { WINED3D_VK_EXT_NONE = 0, WINED3D_VK_EXT_EXTENDED_DYNAMIC_STATE = 1, WINED3D_VK_EXT_EXTENDED_DYNAMIC_STATE2 = 2, WINED3D_VK_EXT_EXTENDED_DYNAMIC_STATE3 = 3, WINED3D_VK_EXT_HOST_QUERY_RESET = 4, WINED3D_VK_EXT_SAMPLER_FILTER_MINMAX = 5, WINED3D_VK_EXT_SHADER_STENCIL_EXPORT = 6, WINED3D_VK_EXT_TRANSFORM_FEEDBACK = 7, WINED3D_VK_EXT_VERTEX_ATTRIBUTE_DIVISOR = 8, WINED3D_VK_KHR_MAINTENANCE2 = 9, WINED3D_VK_KHR_SAMPLER_MIRROR_CLAMP_TO_EDGE = 10, WINED3D_VK_KHR_SAMPLER_YCBCR_CONVERSION = 11, WINED3D_VK_KHR_SHADER_DRAW_PARAMETERS = 12, WINED3D_VK_KHR_VIDEO_DECODE_H264 = 13, WINED3D_VK_KHR_VIDEO_QUEUE = 14, WINED3D_VK_EXT_COUNT = 15 };

_Static_assert(sizeof(struct texture_stage_op) == 16, "tso");
_Static_assert(sizeof(struct ffp_frag_settings) == 132, "ffp");
_Static_assert(sizeof(struct wined3d_state) == 7276, "state");
#define ARG_UNUSED 0xff
#define WINED3DTA_ALPHAREPLICATE 0x00000020
#define WINED3DTA_COMPLEMENT 0x00000010
#define WINED3DTA_CONSTANT 0x00000006
#define WINED3DTA_CURRENT 0x00000001
#define WINED3DTA_DIFFUSE 0x00000000
#define WINED3DTA_SELECTMASK 0x0000000f
#define WINED3DTA_SPECULAR 0x00000004
#define WINED3DTA_TEMP 0x00000005
#define WINED3DTA_TEXTURE 0x00000002
#define WINED3DTA_TFACTOR 0x00000003
#define WINED3D_FORMAT_CAP_SRGB_WRITE 0x00000200
#define WINED3D_LEGACY_CUBEMAP_FILTERING 0x00001000
#define WINED3D_NORMALIZED_DEPTH_BIAS 0x00002000
#define WINED3D_SRGB_READ_WRITE_CONTROL 0x00000200

static const struct color_fixup_desc COLOR_FIXUP_IDENTITY = {0, CHANNEL_SOURCE_X, 0, CHANNEL_SOURCE_Y, 0, CHANNEL_SOURCE_Z, 0, CHANNEL_SOURCE_W};
#define WINED3D_CKEY_SRC_BLT 0x00000008

#define WINED3D_FFP_TCI_SHIFT 16
#define WINED3D_FFP_TCI_MASK 0xffu

static inline BOOL is_complex_fixup(struct color_fixup_desc fixup)
{
    return fixup.x_source == CHANNEL_SOURCE_COMPLEX0 || fixup.x_source == CHANNEL_SOURCE_COMPLEX1;
}

static inline BOOL is_scaling_fixup(struct color_fixup_desc fixup)
{
    return fixup.x_sign_fixup || fixup.y_sign_fixup || fixup.z_sign_fixup || fixup.w_sign_fixup;
}

static inline struct wined3d_texture *wined3d_state_get_ffp_texture(const struct wined3d_state *state, unsigned int idx)
{
    struct wined3d_shader_resource_view *view = state->shader_resource_view[WINED3D_SHADER_TYPE_PIXEL][idx];

    assert(idx <= WINED3D_MAX_FFP_TEXTURES);
    return view ? ((struct wined3d_texture *)((char *)(view->resource) - 0)) : NULL;
}

static inline BOOL use_vs(const struct wined3d_state *state)
{
    /* Check state->vertex_declaration to allow this to be used before the
     * stream info is validated, for example in device_update_tex_unit_map(). */
    return state->shader[WINED3D_SHADER_TYPE_VERTEX]
            && (!state->vertex_declaration || !state->vertex_declaration->position_transformed);
}

static inline BOOL needs_srgb_write(const struct wined3d_d3d_info *d3d_info,
        const struct wined3d_state *state, const struct wined3d_fb_state *fb)
{
    return (!(d3d_info->wined3d_creation_flags & WINED3D_SRGB_READ_WRITE_CONTROL)
            || state->extra_ps_args.srgb_write)
            && fb->render_targets[0] && fb->render_targets[0]->format_caps & WINED3D_FORMAT_CAP_SRGB_WRITE;
}

static inline BOOL can_use_texture_swizzle(const struct wined3d_d3d_info *d3d_info, const struct wined3d_format *format)
{
    return d3d_info->texture_swizzle && !is_complex_fixup(format->color_fixup) && !is_scaling_fixup(format->color_fixup);
}

static inline uint32_t wined3d_mask_from_size(unsigned int size)
{
    return size < 32 ? (1u << size) - 1 : ~0u;
}

BOOL is_invalid_op(const struct wined3d_state *state, int stage,
        enum wined3d_texture_op op, DWORD arg1, DWORD arg2, DWORD arg3)
{
    if (op == WINED3D_TOP_DISABLE)
        return FALSE;
    if (wined3d_state_get_ffp_texture(state, stage))
        return FALSE;

    if ((arg1 & WINED3DTA_SELECTMASK) == WINED3DTA_TEXTURE
            && op != WINED3D_TOP_SELECT_ARG2)
        return TRUE;
    if ((arg2 & WINED3DTA_SELECTMASK) == WINED3DTA_TEXTURE
            && op != WINED3D_TOP_SELECT_ARG1)
        return TRUE;
    if ((arg3 & WINED3DTA_SELECTMASK) == WINED3DTA_TEXTURE
            && (op == WINED3D_TOP_MULTIPLY_ADD || op == WINED3D_TOP_LERP))
        return TRUE;

    return FALSE;
}

void wined3d_ffp_get_fs_settings(const struct wined3d_state *state,
        const struct wined3d_d3d_info *d3d_info, struct ffp_frag_settings *settings)
{
#define ARG1 0x01
#define ARG2 0x02
#define ARG0 0x04
    static const unsigned char args[WINED3D_TOP_LERP + 1] =
    {
        /* undefined                        */  0,
        /* D3DTOP_DISABLE                   */  0,
        /* D3DTOP_SELECTARG1                */  ARG1,
        /* D3DTOP_SELECTARG2                */  ARG2,
        /* D3DTOP_MODULATE                  */  ARG1 | ARG2,
        /* D3DTOP_MODULATE2X                */  ARG1 | ARG2,
        /* D3DTOP_MODULATE4X                */  ARG1 | ARG2,
        /* D3DTOP_ADD                       */  ARG1 | ARG2,
        /* D3DTOP_ADDSIGNED                 */  ARG1 | ARG2,
        /* D3DTOP_ADDSIGNED2X               */  ARG1 | ARG2,
        /* D3DTOP_SUBTRACT                  */  ARG1 | ARG2,
        /* D3DTOP_ADDSMOOTH                 */  ARG1 | ARG2,
        /* D3DTOP_BLENDDIFFUSEALPHA         */  ARG1 | ARG2,
        /* D3DTOP_BLENDTEXTUREALPHA         */  ARG1 | ARG2,
        /* D3DTOP_BLENDFACTORALPHA          */  ARG1 | ARG2,
        /* D3DTOP_BLENDTEXTUREALPHAPM       */  ARG1 | ARG2,
        /* D3DTOP_BLENDCURRENTALPHA         */  ARG1 | ARG2,
        /* D3DTOP_PREMODULATE               */  ARG1 | ARG2,
        /* D3DTOP_MODULATEALPHA_ADDCOLOR    */  ARG1 | ARG2,
        /* D3DTOP_MODULATECOLOR_ADDALPHA    */  ARG1 | ARG2,
        /* D3DTOP_MODULATEINVALPHA_ADDCOLOR */  ARG1 | ARG2,
        /* D3DTOP_MODULATEINVCOLOR_ADDALPHA */  ARG1 | ARG2,
        /* D3DTOP_BUMPENVMAP                */  ARG1 | ARG2,
        /* D3DTOP_BUMPENVMAPLUMINANCE       */  ARG1 | ARG2,
        /* D3DTOP_DOTPRODUCT3               */  ARG1 | ARG2,
        /* D3DTOP_MULTIPLYADD               */  ARG1 | ARG2 | ARG0,
        /* D3DTOP_LERP                      */  ARG1 | ARG2 | ARG0
    };
    unsigned int i;
    DWORD cop, aop, carg0, carg1, carg2, aarg0, aarg1, aarg2;
    struct wined3d_texture *texture;

    settings->padding = 0;

    for (i = 0; i < d3d_info->ffp_fragment_caps.max_blend_stages; ++i)
    {
        settings->op[i].padding = 0;
        if (state->texture_states[i][WINED3D_TSS_COLOR_OP] == WINED3D_TOP_DISABLE)
        {
            settings->op[i].cop = WINED3D_TOP_DISABLE;
            settings->op[i].aop = WINED3D_TOP_DISABLE;
            settings->op[i].carg0 = settings->op[i].carg1 = settings->op[i].carg2 = ARG_UNUSED;
            settings->op[i].aarg0 = settings->op[i].aarg1 = settings->op[i].aarg2 = ARG_UNUSED;
            settings->op[i].color_fixup = COLOR_FIXUP_IDENTITY;
            settings->op[i].tmp_dst = 0;
            settings->op[i].tex_type = WINED3D_GL_RES_TYPE_TEX_1D;
            settings->op[i].projected = 0;
            i++;
            break;
        }

        if ((texture = wined3d_state_get_ffp_texture(state, i)))
        {
            if (can_use_texture_swizzle(d3d_info, texture->resource.format))
                settings->op[i].color_fixup = COLOR_FIXUP_IDENTITY;
            else
                settings->op[i].color_fixup = texture->resource.format->color_fixup;
            settings->op[i].tex_type = texture->resource.gl_type;
        } else {
            settings->op[i].color_fixup = COLOR_FIXUP_IDENTITY;
            settings->op[i].tex_type = WINED3D_GL_RES_TYPE_TEX_1D;
        }

        cop = state->texture_states[i][WINED3D_TSS_COLOR_OP];
        aop = state->texture_states[i][WINED3D_TSS_ALPHA_OP];

        carg1 = (args[cop] & ARG1) ? state->texture_states[i][WINED3D_TSS_COLOR_ARG1] : ARG_UNUSED;
        carg2 = (args[cop] & ARG2) ? state->texture_states[i][WINED3D_TSS_COLOR_ARG2] : ARG_UNUSED;
        carg0 = (args[cop] & ARG0) ? state->texture_states[i][WINED3D_TSS_COLOR_ARG0] : ARG_UNUSED;

        if (is_invalid_op(state, i, cop, carg1, carg2, carg0))
        {
            carg0 = ARG_UNUSED;
            carg2 = ARG_UNUSED;
            carg1 = WINED3DTA_CURRENT;
            cop = WINED3D_TOP_SELECT_ARG1;
        }

        if (cop == WINED3D_TOP_DOTPRODUCT3)
        {
            /* A dotproduct3 on the colorop overwrites the alphaop operation and replicates
             * the color result to the alpha component of the destination
             */
            aop = cop;
            aarg1 = carg1;
            aarg2 = carg2;
            aarg0 = carg0;
        }
        else
        {
            aarg1 = (args[aop] & ARG1) ? state->texture_states[i][WINED3D_TSS_ALPHA_ARG1] : ARG_UNUSED;
            aarg2 = (args[aop] & ARG2) ? state->texture_states[i][WINED3D_TSS_ALPHA_ARG2] : ARG_UNUSED;
            aarg0 = (args[aop] & ARG0) ? state->texture_states[i][WINED3D_TSS_ALPHA_ARG0] : ARG_UNUSED;
        }

        if (is_invalid_op(state, i, aop, aarg1, aarg2, aarg0))
        {
               aarg0 = ARG_UNUSED;
               aarg2 = ARG_UNUSED;
               aarg1 = WINED3DTA_CURRENT;
               aop = WINED3D_TOP_SELECT_ARG1;
        }

        settings->op[i].projected = (carg1 == WINED3DTA_TEXTURE || carg2 == WINED3DTA_TEXTURE || carg0 == WINED3DTA_TEXTURE
                || aarg1 == WINED3DTA_TEXTURE || aarg2 == WINED3DTA_TEXTURE || aarg0 == WINED3DTA_TEXTURE)
                && (state->texture_states[i][WINED3D_TSS_TEXTURE_TRANSFORM_FLAGS] & WINED3D_TTFF_PROJECTED);

        settings->op[i].cop = cop;
        settings->op[i].aop = aop;
        settings->op[i].carg0 = carg0;
        settings->op[i].carg1 = carg1;
        settings->op[i].carg2 = carg2;
        settings->op[i].aarg0 = aarg0;
        settings->op[i].aarg1 = aarg1;
        settings->op[i].aarg2 = aarg2;
        settings->op[i].tmp_dst = state->texture_states[i][WINED3D_TSS_RESULT_ARG] == WINED3DTA_TEMP;
    }

    /* Clear unsupported stages */
    for (; i < WINED3D_MAX_FFP_TEXTURES; ++i)
        memset(&settings->op[i], 0xff, sizeof(settings->op[i]));

    if (!state->extra_ps_args.fog_enable)
    {
        settings->fog = WINED3D_FFP_PS_FOG_OFF;
    }
    else if (state->extra_ps_args.fog_mode == WINED3D_FOG_NONE)
    {
        if (use_vs(state) || state->vertex_declaration->position_transformed)
        {
            settings->fog = WINED3D_FFP_PS_FOG_LINEAR;
        }
        else
        {
            switch (state->render_states[WINED3D_RS_FOGVERTEXMODE])
            {
                case WINED3D_FOG_NONE:
                case WINED3D_FOG_LINEAR:
                    settings->fog = WINED3D_FFP_PS_FOG_LINEAR;
                    break;
                case WINED3D_FOG_EXP:
                    settings->fog = WINED3D_FFP_PS_FOG_EXP;
                    break;
                case WINED3D_FOG_EXP2:
                    settings->fog = WINED3D_FFP_PS_FOG_EXP2;
                    break;
            }
        }
    }
    else
    {
        switch (state->extra_ps_args.fog_mode)
        {
            case WINED3D_FOG_LINEAR:
                settings->fog = WINED3D_FFP_PS_FOG_LINEAR;
                break;
            case WINED3D_FOG_EXP:
                settings->fog = WINED3D_FFP_PS_FOG_EXP;
                break;
            case WINED3D_FOG_EXP2:
                settings->fog = WINED3D_FFP_PS_FOG_EXP2;
                break;
            case WINED3D_FOG_NONE:
                /* unreachable */
                break;
        }
    }
    settings->sRGB_write = !d3d_info->srgb_write_control && needs_srgb_write(d3d_info, state, &state->fb);

    texture = wined3d_state_get_ffp_texture(state, 0);
    if (state->render_states[WINED3D_RS_COLORKEYENABLE]
            && texture && (texture->async.color_key_flags & WINED3D_CKEY_SRC_BLT)
            && settings->op[0].cop != WINED3D_TOP_DISABLE)
        settings->color_key_enabled = 1;
    else
        settings->color_key_enabled = 0;

    /* texcoords_initialized is set to meaningful values only when GL doesn't
     * support enough varyings to always pass around all the possible texture
     * coordinates.
     * This is used to avoid reading a varying not written by the vertex shader.
     * Reading uninitialized varyings on core profile contexts results in an
     * error while with builtin varyings on legacy contexts you get undefined
     * behavior. */
    if (d3d_info->limits.varying_count && !d3d_info->full_ffp_varyings)
    {
        settings->texcoords_initialized = 0;
        for (i = 0; i < WINED3D_MAX_FFP_TEXTURES; ++i)
        {
            if (use_vs(state))
            {
                if (state->shader[WINED3D_SHADER_TYPE_VERTEX]->reg_maps.output_registers & (1u << i))
                    settings->texcoords_initialized |= 1u << i;
            }
            else
            {
                unsigned int coord_idx = state->texture_states[i][WINED3D_TSS_TEXCOORD_INDEX];
                if ((state->texture_states[i][WINED3D_TSS_TEXCOORD_INDEX] >> WINED3D_FFP_TCI_SHIFT)
                        & WINED3D_FFP_TCI_MASK
                        || (coord_idx < WINED3D_MAX_FFP_TEXTURES && (state->vertex_declaration->texcoords & (1u << coord_idx))))
                    settings->texcoords_initialized |= 1u << i;
            }
        }
    }
    else
    {
        settings->texcoords_initialized = wined3d_mask_from_size(WINED3D_MAX_FFP_TEXTURES);
    }

    settings->pointsprite = state->extra_ps_args.point_sprite
            && state->primitive_type == WINED3D_PT_POINTLIST;

    if (d3d_info->ffp_alpha_test)
        settings->alpha_test_func = WINED3D_CMP_ALWAYS - 1;
    else
        settings->alpha_test_func = state->extra_ps_args.alpha_func - 1;

    if (d3d_info->emulated_flatshading)
        settings->flatshading = state->extra_ps_args.flat_shading;
    else
        settings->flatshading = FALSE;
}
