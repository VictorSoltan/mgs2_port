// SPDX-License-Identifier: MIT
//
// One-shot Mali hardware-counter capture for the RG353VS.
//
// This intentionally does no output while the measured window is active.  It
// enables the counters, accumulates them in the kernel, sleeps, requests one
// sample, and prints only after the window has ended.  That keeps measurement
// I/O off the game and graphics hot paths.
//
// Build against Arm's official gator/hwcpipe2 device library.  The exact gator
// revision and the temporary build compatibility changes used for the first
// deployed binary are recorded in the accompanying performance brief.

#include <device/handle.hpp>
#include <device/hwcnt/block_extents.hpp>
#include <device/hwcnt/sample.hpp>
#include <device/hwcnt/sampler/configuration.hpp>
#include <device/hwcnt/sampler/manual.hpp>
#include <device/instance.hpp>

#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <system_error>
#include <thread>
#include <vector>

namespace dev = hwcpipe::device;
namespace hw = hwcpipe::device::hwcnt;

static const char *block_name(hw::block_type type)
{
    switch (type)
    {
        case hw::block_type::fe: return "jm";
        case hw::block_type::tiler: return "tiler";
        case hw::block_type::memory: return "memory";
        case hw::block_type::core: return "shader";
        case hw::block_type::firmware: return "firmware";
        case hw::block_type::csg: return "csg";
    }
    return "unknown";
}

int main(int argc, char **argv)
{
    const unsigned seconds = argc > 1 ? std::strtoul(argv[1], nullptr, 10) : 10;
    if (!seconds || seconds > 3600)
    {
        std::fprintf(stderr, "duration must be between 1 and 3600 seconds\n");
        return 1;
    }

    auto handle = dev::handle::create();
    if (!handle)
    {
        std::fprintf(stderr, "handle failed\n");
        return 2;
    }
    auto instance = dev::instance::create(*handle);
    if (!instance)
    {
        std::fprintf(stderr, "instance failed\n");
        return 3;
    }

    const auto extents = instance->get_hwcnt_block_extents();
    hw::sampler::configuration::enable_map_type all;
    all.set();
    std::vector<hw::sampler::configuration> configs;
    for (int i = static_cast<int>(hw::block_type::first);
            i <= static_cast<int>(hw::block_type::last); ++i)
    {
        const auto type = static_cast<hw::block_type>(i);
        if (extents.num_blocks_of_type(type))
            configs.push_back({type, hw::prfcnt_set::primary, all});
    }

    hw::sampler::manual sampler(*instance, configs.data(), configs.size());
    if (!sampler)
    {
        std::fprintf(stderr, "sampler failed\n");
        return 4;
    }
    if (auto ec = sampler.accumulation_start())
    {
        std::fprintf(stderr, "start failed: %s\n", ec.message().c_str());
        return 5;
    }

    std::this_thread::sleep_for(std::chrono::seconds(seconds));
    if (auto ec = sampler.request_sample(0))
    {
        std::fprintf(stderr, "request failed: %s\n", ec.message().c_str());
        return 6;
    }

    std::error_code ec;
    {
        hw::sample sample(sampler.get_reader(), ec);
        if (ec)
        {
            std::fprintf(stderr, "sample failed: %s\n", ec.message().c_str());
            return 7;
        }
        const auto &meta = sample.get_metadata();
        std::printf("meta seconds=%u begin_ns=%llu end_ns=%llu gpu_cycle=%llu "
                    "sc_cycle=%llu stretched=%u error=%u counters=%u type=%u\n",
                seconds,
                static_cast<unsigned long long>(meta.timestamp_ns_begin),
                static_cast<unsigned long long>(meta.timestamp_ns_end),
                static_cast<unsigned long long>(meta.gpu_cycle),
                static_cast<unsigned long long>(meta.sc_cycle),
                meta.flags.stretched, meta.flags.error,
                extents.counters_per_block(),
                static_cast<unsigned>(extents.values_type()));
        for (const auto block : sample.blocks())
        {
            std::printf("block %s index=%u on=%u available=%u",
                    block_name(block.type), block.index,
                    block.state.on, block.state.available);
            if (extents.values_type() == hw::sample_values_type::uint64)
            {
                const auto *values =
                        static_cast<const std::uint64_t *>(block.values);
                for (unsigned i = 0; i < extents.counters_per_block(); ++i)
                    std::printf(" %u=%llu", i,
                            static_cast<unsigned long long>(values[i]));
            }
            else
            {
                const auto *values =
                        static_cast<const std::uint32_t *>(block.values);
                for (unsigned i = 0; i < extents.counters_per_block(); ++i)
                    std::printf(" %u=%u", i, values[i]);
            }
            std::putchar('\n');
        }
    }
    if (ec)
    {
        std::fprintf(stderr, "put sample failed: %s\n", ec.message().c_str());
        return 8;
    }
    if (auto stop_ec = sampler.accumulation_stop(0))
    {
        std::fprintf(stderr, "stop failed: %s\n", stop_ec.message().c_str());
        return 9;
    }
    return 0;
}
