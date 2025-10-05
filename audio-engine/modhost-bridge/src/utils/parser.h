#pragma once

#include "types.h"
#include <string>
#include <optional>

namespace modhost_bridge {

/**
 * Parse a feedback line from mod-host into a structured FeedbackMessage.
 *
 * @param line The raw feedback line from mod-host
 * @return Parsed FeedbackMessage or std::nullopt if parsing failed
 */
std::optional<FeedbackMessage> parse_feedback_line(const std::string& line);

} // namespace modhost_bridge