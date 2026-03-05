def split_train_validation(samples: list[object], validation_ratio: float = 0.2) -> tuple[list[object], list[object]]:
    if not samples:
        return [], []
    ratio = min(0.9, max(0.0, validation_ratio))
    split_at = int(len(samples) * (1.0 - ratio))
    split_at = max(1, min(split_at, len(samples)))
    return samples[:split_at], samples[split_at:]
