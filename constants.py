index_options = [
    "VNINDEX",
    "VN30",
    "VNMidCap",
    "VN100",
    "HNX30",
    "UPCOM",
]

# Mapping co dinh theo vi tri: index_options[i] -> quote_symbols[i], group_symbols[i]
quote_symbols = [
    "VNINDEX",
    "VN30",
    "VNMidCap",
    "VN100",
    "HNX30",
    "UpComIndex",
]

group_symbols = [
    "VNINDEX",
    "VN30",
    "VNMidCap",
    "VN100",
    "HNX30",
    "UPCOM",
]

GROUP_ELIGIBLE = {
    "HOSE",
    "VN30",
    "VNMidCap",
    "VN100",
    "HNX30",
    "UPCOM",
}

INDEX_TO_QUOTE = dict(zip(index_options, quote_symbols))

__all__ = [
    "index_options",
    "quote_symbols",
    "group_symbols",
    "GROUP_ELIGIBLE",
    "INDEX_TO_QUOTE",
]
