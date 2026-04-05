//! # Phenotype Iter
//!
//! Iterator extensions and utilities for common patterns.
//!
//! ## Features
//!
//! - Chunking iterators
//! - Windowed iteration
//! - Batch processing
//! - Unique filtering
//!
//! ## Example
//!
//! ```rust
//! use phenotype_iter::IteratorExt;
//!
//! let data = vec![1, 2, 3, 4, 5];
//! let chunks: Vec<Vec<_>> = data.into_iter().chunks(2).collect();
//! ```

/// Extension trait for iterators
pub trait IteratorExt: Iterator + Sized {
    /// Chunk iterator into fixed-size groups
    fn chunks(self, size: usize) -> Chunks<Self>;

    /// Get sliding windows of given size
    fn windows(self, size: usize) -> Windows<Self>;

    /// Filter consecutive duplicates
    fn dedup_consecutive(self) -> DedupConsecutive<Self>
    where
        Self::Item: PartialEq;

    /// Batch process with size limit
    fn batches(self, size: usize) -> Batches<Self>;
}

impl<I: Iterator> IteratorExt for I {
    fn chunks(self, size: usize) -> Chunks<Self> {
        Chunks { inner: self, size }
    }

    fn windows(self, size: usize) -> Windows<Self> {
        Windows {
            inner: self,
            size,
            buffer: Vec::new(),
        }
    }

    fn dedup_consecutive(self) -> DedupConsecutive<Self>
    where
        Self::Item: PartialEq,
    {
        DedupConsecutive {
            inner: self,
            last: None,
        }
    }

    fn batches(self, size: usize) -> Batches<Self> {
        Batches { inner: self, size }
    }
}

/// Chunked iterator
pub struct Chunks<I> {
    inner: I,
    size: usize,
}

impl<I: Iterator> Iterator for Chunks<I> {
    type Item = Vec<I::Item>;

    fn next(&mut self) -> Option<Self::Item> {
        let mut chunk = Vec::with_capacity(self.size);

        while chunk.len() < self.size {
            match self.inner.next() {
                Some(item) => chunk.push(item),
                None => break,
            }
        }

        if chunk.is_empty() {
            None
        } else {
            Some(chunk)
        }
    }
}

/// Windowed iterator
/// Window iterator adapter
pub struct Windows<I: Iterator> {
    inner: I,
    size: usize,
    buffer: Vec<I::Item>,
}

impl<I: Iterator> Iterator for Windows<I>
where
    I::Item: Clone,
{
    type Item = Vec<I::Item>;

    fn next(&mut self) -> Option<Self::Item> {
        // Fill buffer to size
        while self.buffer.len() < self.size {
            match self.inner.next() {
                Some(item) => self.buffer.push(item),
                None => break,
            }
        }

        if self.buffer.len() == self.size {
            let window = self.buffer.clone();
            self.buffer.remove(0);
            Some(window)
        } else {
            None
        }
    }
}

/// Consecutive deduplication iterator
pub struct DedupConsecutive<I: Iterator> {
    inner: I,
    last: Option<I::Item>,
}

impl<I: Iterator> Iterator for DedupConsecutive<I>
where
    I::Item: PartialEq + Clone,
{
    type Item = I::Item;

    fn next(&mut self) -> Option<Self::Item> {
        loop {
            match self.inner.next() {
                Some(item) => {
                    if self.last.as_ref() != Some(&item) {
                        self.last = Some(item.clone());
                        return Some(item);
                    }
                }
                None => return None,
            }
        }
    }
}

/// Batch processing iterator
pub struct Batches<I> {
    inner: I,
    size: usize,
}

impl<I: Iterator> Iterator for Batches<I> {
    type Item = Vec<I::Item>;

    fn next(&mut self) -> Option<Self::Item> {
        let mut batch = Vec::with_capacity(self.size);

        while batch.len() < self.size {
            match self.inner.next() {
                Some(item) => batch.push(item),
                None => break,
            }
        }

        if batch.is_empty() {
            None
        } else {
            Some(batch)
        }
    }
}

/// Collect into chunks
pub fn into_chunks<T>(items: Vec<T>, size: usize) -> Vec<Vec<T>> {
    items.into_iter().chunks(size).collect()
}

/// Process items in parallel batches (requires rayon feature)
#[cfg(feature = "parallel")]
pub fn parallel_batch_process<T, F, R>(items: Vec<T>, batch_size: usize, f: F) -> Vec<R>
where
    T: Send,
    R: Send,
    F: Fn(T) -> R + Send + Sync,
{
    use rayon::prelude::*;

    items
        .into_par_iter()
        .chunks(batch_size)
        .flat_map(|chunk| chunk.into_iter().map(&f).collect::<Vec<_>>())
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_chunks() {
        let data = vec![1, 2, 3, 4, 5];
        let chunks: Vec<Vec<_>> = data.into_iter().chunks(2).collect();
        assert_eq!(chunks, vec![vec![1, 2], vec![3, 4], vec![5]]);
    }

    #[test]
    fn test_windows() {
        let data = vec![1, 2, 3, 4, 5];
        let windows: Vec<Vec<_>> = data.into_iter().windows(3).collect();
        assert_eq!(windows, vec![vec![1, 2, 3], vec![2, 3, 4], vec![3, 4, 5],]);
    }

    #[test]
    fn test_dedup_consecutive() {
        let data = vec![1, 1, 2, 2, 2, 3, 3, 1];
        let deduped: Vec<_> = data.into_iter().dedup_consecutive().collect();
        assert_eq!(deduped, vec![1, 2, 3, 1]);
    }

    #[test]
    fn test_batches() {
        let data = vec![1, 2, 3, 4, 5, 6, 7];
        let batches: Vec<Vec<_>> = data.into_iter().batches(3).collect();
        assert_eq!(batches, vec![vec![1, 2, 3], vec![4, 5, 6], vec![7]]);
    }

    #[test]
    fn test_into_chunks() {
        let data = vec!["a", "b", "c", "d", "e"];
        let chunks = into_chunks(data, 2);
        assert_eq!(chunks, vec![vec!["a", "b"], vec!["c", "d"], vec!["e"]]);
    }
}
