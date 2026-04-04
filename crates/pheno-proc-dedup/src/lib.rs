//! Data deduplication for stream processing

use std::collections::HashSet;
use std::hash::Hash;

/// Deduplication filter using HashSet
#[derive(Debug, Default)]
pub struct DedupFilter<T: Hash + Eq> {
    seen: HashSet<T>,
}

impl<T: Hash + Eq> DedupFilter<T> {
    pub fn new() -> Self {
        Self {
            seen: HashSet::new(),
        }
    }

    pub fn with_capacity(capacity: usize) -> Self {
        Self {
            seen: HashSet::with_capacity(capacity),
        }
    }

    pub fn check_and_insert(&mut self, item: T) -> bool {
        self.seen.insert(item)
    }

    pub fn clear(&mut self) {
        self.seen.clear();
    }

    pub fn len(&self) -> usize {
        self.seen.len()
    }

    pub fn is_empty(&self) -> bool {
        self.seen.is_empty()
    }
}

/// Bloom filter for probabilistic deduplication
pub struct BloomFilter {
    bits: Vec<bool>,
    size: usize,
    hash_count: usize,
}

impl BloomFilter {
    pub fn new(size: usize, hash_count: usize) -> Self {
        Self {
            bits: vec![false; size],
            size,
            hash_count,
        }
    }

    pub fn add(&mut self, item: &[u8]) {
        for i in 0..self.hash_count {
            let idx = self.hash(item, i) % self.size;
            self.bits[idx] = true;
        }
    }

    pub fn check(&self, item: &[u8]) -> bool {
        for i in 0..self.hash_count {
            let idx = self.hash(item, i) % self.size;
            if !self.bits[idx] {
                return false;
            }
        }
        true
    }

    pub fn check_and_add(&mut self, item: &[u8]) -> bool {
        let exists = self.check(item);
        if !exists {
            self.add(item);
        }
        exists
    }

    fn hash(&self, item: &[u8], seed: usize) -> usize {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};

        let mut hasher = DefaultHasher::new();
        item.hash(&mut hasher);
        seed.hash(&mut hasher);
        hasher.finish() as usize
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dedup_filter() {
        let mut filter = DedupFilter::<i32>::new();
        assert!(filter.check_and_insert(1));
        assert!(!filter.check_and_insert(1)); // Already seen
        assert!(filter.check_and_insert(2));
        assert_eq!(filter.len(), 2);
    }

    #[test]
    fn test_bloom_filter() {
        let mut filter = BloomFilter::new(1000, 3);
        let item = b"test data";

        assert!(!filter.check(item)); // Should be false initially
        filter.add(item);
        assert!(filter.check(item)); // Should be true after adding
    }
}
