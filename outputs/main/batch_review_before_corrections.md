# Batch Review of 30 Main-Study Tasks

**This is AI-assisted review, not completed human review.**
Generated from `src/batch_review.py` using an independent oracle for each task.
All human-review statuses remain pending.

## Summary Table

| ID | Category | Function | Status |
|-----|----------|----------|--------|
| m01 | string processing | `count_vowels(s)` | no issue |
| m02 | string processing | `is_palindrome(s)` | no issue |
| m03 | string processing | `count_occurrences(s, c)` | no issue |
| m04 | string processing | `uppercase_first(s)` | no issue |
| m05 | string processing | `replace_char(s, old, new)` | no issue |
| m06 | list transformations | `double_all(values)` | no issue |
| m07 | list transformations | `interleave(list1, list2)` | no issue |
| m08 | list transformations | `sum_list(values)` | no issue |
| m09 | list transformations | `cumulative_sum(values)` | no issue |
| m10 | list transformations | `rotate_left(values, k)` | no issue |
| m11 | dictionary/counting operations | `char_frequency(s)` | no issue |
| m12 | dictionary/counting operations | `invert_dict(d)` | no issue |
| m13 | dictionary/counting operations | `merge_dicts(d1, d2)` | no issue |
| m14 | dictionary/counting operations | `most_frequent(values)` | no issue |
| m15 | dictionary/counting operations | `count_by_parity(values)` | no issue |
| m16 | searching and index handling | `find_all_indices(values, target)` | no issue |
| m17 | searching and index handling | `binary_search(sorted_list, target)` | no issue |
| m18 | searching and index handling | `first_above(values, threshold)` | no issue |
| m19 | searching and index handling | `is_sorted(values)` | no issue |
| m20 | searching and index handling | `longest_run(values)` | no issue |
| m21 | integer arithmetic and boundaries | `power_of_two(n)` | no issue |
| m22 | integer arithmetic and boundaries | `ceil_div(a, b)` | no issue |
| m23 | integer arithmetic and boundaries | `digit_sum(n)` | no issue |
| m24 | integer arithmetic and boundaries | `count_digits(n)` | no issue |
| m25 | integer arithmetic and boundaries | `is_perfect_square(n)` | no issue |
| m26 | small algorithms | `is_anagram(s1, s2)` | no issue |
| m27 | small algorithms | `kth_smallest(values, k)` | no issue |
| m28 | small algorithms | `has_duplicate(values)` | no issue |
| m29 | small algorithms | `sorted_intersection(list1, list2)` | no issue |
| m30 | small algorithms | `count_even_sum_pairs(values)` | no issue |

**Tasks reviewed:** 30
**Tasks with issues:** 0

## Shared Validation Gaps

- None found. The independent oracle agrees with all 240 stored expected values.
- No code comments or docstrings reveal correctness status.
- No prompt privacy violations detected.
- No pilot task overlap in signatures or problem statements.
- All tasks have boundary/edge cases.

## Proposed Fixes

No fixes required.

## Per-Task Review

### m01 — count_vowels(s)

**Specification:** Return the number of vowels (a, e, i, o, u) in string s, counted case-insensitively. s is any Python string, including an empty string.

**Reference:**
```python
def count_vowels(s):
    count = 0
    for ch in s:
        if ch.lower() in "aeiou":
            count += 1
    return count
```

**Faulty:**
```python
def count_vowels(s):
    count = 0
    for ch in s:
        if ch in "aeiou":
            count += 1
    return count
```

**Named counterexample** (`uppercase_vowels`, kind=adversarial):
- Input: `['HELLO']`
- Expected: `2`
- Faulty output: `0`

**Ordinary passing input for faulty:** `lowercase_only`

**Reference correctness:** The reference correctly iterates over each character, lowercases it, and checks against the vowel set

**Boundary cases checked:** empty_string, all_vowels_upper, single_uppercase_vowel

**Findings:** no issue

### m02 — is_palindrome(s)

**Specification:** Return True if s is a palindrome (reads the same forwards and backwards), case-insensitively. s is any Python string, including an empty string.

**Reference:**
```python
def is_palindrome(s):
    s = s.lower()
    left = 0
    right = len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True
```

**Faulty:**
```python
def is_palindrome(s):
    left = 0
    right = len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True
```

**Named counterexample** (`mixed_case_palindrome`, kind=adversarial):
- Input: `['Racecar']`
- Expected: `True`
- Faulty output: `False`

**Ordinary passing input for faulty:** `lowercase_palindrome`

**Reference correctness:** The reference correctly lowercases the string and compares characters from both ends moving inward

**Boundary cases checked:** empty_string, single_char, upper_mixed_palindrome

**Findings:** no issue

### m03 — count_occurrences(s, c)

**Specification:** Return the number of times character c appears in string s. s is any Python string (including empty); c is a single character string.

**Reference:**
```python
def count_occurrences(s, c):
    count = 0
    for ch in s:
        if ch == c:
            count += 1
    return count
```

**Faulty:**
```python
def count_occurrences(s, c):
    count = 0
    for ch in s:
        if ch == c:
            count = 1
    return count
```

**Named counterexample** (`two_occurrences`, kind=ordinary):
- Input: `['hello', 'l']`
- Expected: `2`
- Faulty output: `1`

**Ordinary passing input for faulty:** `single_occurrence`

**Reference correctness:** The reference correctly iterates over each character and increments a counter on match

**Boundary cases checked:** empty_string, single_char_match

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m04 — uppercase_first(s)

**Specification:** Return a copy of s with the first character uppercased and all remaining characters unchanged. If s is empty, return the empty string. s is any Python string.

**Reference:**
```python
def uppercase_first(s):
    if len(s) == 0:
        return s
    return s[0].upper() + s[1:]
```

**Faulty:**
```python
def uppercase_first(s):
    if len(s) == 0:
        return s
    return s[0].upper() + s[1:].lower()
```

**Named counterexample** (`mixed_case_rest`, kind=adversarial):
- Input: `['hELLO']`
- Expected: `HELLO`
- Faulty output: `Hello`

**Ordinary passing input for faulty:** `lowercase`

**Reference correctness:** The reference correctly uppercases only the first character and leaves the rest unchanged

**Boundary cases checked:** empty, single_char, all_upper

**Findings:** no issue

### m05 — replace_char(s, old, new)

**Specification:** Return a copy of s where every occurrence of character old is replaced with character new. Characters not equal to old are left unchanged. s is any Python string; old and new are single character strings.

**Reference:**
```python
def replace_char(s, old, new):
    result = ""
    for ch in s:
        if ch == old:
            result = result + new
        else:
            result = result + ch
    return result
```

**Faulty:**
```python
def replace_char(s, old, new):
    result = ""
    for ch in s:
        if ch == old:
            result = result + old
        else:
            result = result + ch
    return result
```

**Named counterexample** (`replace_l`, kind=ordinary):
- Input: `['hello', 'l', 'x']`
- Expected: `hexxo`
- Faulty output: `hello`

**Ordinary passing input for faulty:** `no_target`

**Reference correctness:** The reference correctly builds a new string character by character, replacing matches with new

**Boundary cases checked:** empty_string, single_replace

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m06 — double_all(values)

**Specification:** Return a new list where each element of values is multiplied by 2. values is any Python list of integers (excluding bool), including an empty list. Do not modify the input.

**Reference:**
```python
def double_all(values):
    result = []
    for v in values:
        result.append(v * 2)
    return result
```

**Faulty:**
```python
def double_all(values):
    result = []
    for v in values:
        result.append(v + 2)
    return result
```

**Named counterexample** (`simple_values`, kind=ordinary):
- Input: `[[1, 2, 3]]`
- Expected: `[2, 4, 6]`
- Faulty output: `[3, 4, 5]`

**Ordinary passing input for faulty:** `twos_only`

**Reference correctness:** The reference correctly iterates over values and appends each element multiplied by 2

**Boundary cases checked:** zero, empty

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m07 — interleave(list1, list2)

**Specification:** Return a new list interleaving elements of list1 and list2, taking one element from list1 then one from list2, in order. Both lists have the same length. list1 and list2 are Python lists of integers. Do not modify the inputs.

**Reference:**
```python
def interleave(list1, list2):
    result = []
    for i in range(len(list1)):
        result.append(list1[i])
        result.append(list2[i])
    return result
```

**Faulty:**
```python
def interleave(list1, list2):
    result = []
    for i in range(len(list1)):
        result.append(list2[i])
        result.append(list1[i])
    return result
```

**Named counterexample** (`distinct_values`, kind=ordinary):
- Input: `[[1, 2], [3, 4]]`
- Expected: `[1, 3, 2, 4]`
- Faulty output: `[3, 1, 4, 2]`

**Ordinary passing input for faulty:** `same_values`

**Reference correctness:** The reference correctly iterates by index and appends list1[i] then list2[i] in order

**Boundary cases checked:** empty_lists, single_pair

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m08 — sum_list(values)

**Specification:** Return the sum of all integers in values. values is any Python list of integers (excluding bool), including an empty list. For an empty list return 0. Do not modify the input.

**Reference:**
```python
def sum_list(values):
    total = 0
    for v in values:
        total += v
    return total
```

**Faulty:**
```python
def sum_list(values):
    total = 0
    for v in values[1:]:
        total += v
    return total
```

**Named counterexample** (`skip_first`, kind=ordinary):
- Input: `[[1, 2, 3]]`
- Expected: `6`
- Faulty output: `5`

**Ordinary passing input for faulty:** `zero_first`

**Reference correctness:** The reference correctly accumulates all elements into a running total starting from 0

**Boundary cases checked:** empty, single

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m09 — cumulative_sum(values)

**Specification:** Return a new list of cumulative sums of values: the i-th element is the sum of values[0] through values[i]. values is any Python list of integers (excluding bool), including an empty list. For an empty list return an empty list. Do not modify the input.

**Reference:**
```python
def cumulative_sum(values):
    result = []
    total = 0
    for v in values:
        total += v
        result.append(total)
    return result
```

**Faulty:**
```python
def cumulative_sum(values):
    result = []
    total = 0
    for v in values:
        total += v
        result.append(v)
    return result
```

**Named counterexample** (`simple`, kind=ordinary):
- Input: `[[1, 2, 3]]`
- Expected: `[1, 3, 6]`
- Faulty output: `[1, 2, 3]`

**Ordinary passing input for faulty:** `zeros`

**Reference correctness:** The reference correctly maintains a running total and appends it after each element

**Boundary cases checked:** empty, single

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m10 — rotate_left(values, k)

**Specification:** Return a new list with the elements of values rotated left by k positions. A left rotation by k moves each element k positions toward the front, wrapping around. values is a Python list of integers (excluding bool); k is a non-negative integer. For an empty list return an empty list. Do not modify the input.

**Reference:**
```python
def rotate_left(values, k):
    n = len(values)
    if n == 0:
        return []
    result = [0] * n
    for i in range(n):
        result[(i - k) % n] = values[i]
    return result
```

**Faulty:**
```python
def rotate_left(values, k):
    n = len(values)
    if n == 0:
        return []
    result = [0] * n
    for i in range(n):
        result[(i + k) % n] = values[i]
    return result
```

**Named counterexample** (`rotate_one`, kind=ordinary):
- Input: `[[1, 2, 3, 4], 1]`
- Expected: `[2, 3, 4, 1]`
- Faulty output: `[4, 1, 2, 3]`

**Ordinary passing input for faulty:** `no_rotation`

**Reference correctness:** The reference correctly places each element at position (i-k)%n, achieving a left rotation by k

**Boundary cases checked:** empty, single

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m11 — char_frequency(s)

**Specification:** Return a dictionary mapping each character in s to the number of times it appears. s is any Python string, including an empty string. For an empty string return an empty dictionary.

**Reference:**
```python
def char_frequency(s):
    result = {}
    for ch in s:
        if ch in result:
            result[ch] += 1
        else:
            result[ch] = 1
    return result
```

**Faulty:**
```python
def char_frequency(s):
    result = {}
    for ch in s:
        if ch in result:
            result[ch] = 1
        else:
            result[ch] = 1
    return result
```

**Named counterexample** (`with_repeats`, kind=ordinary):
- Input: `['hello']`
- Expected: `{'h': 1, 'e': 1, 'l': 2, 'o': 1}`
- Faulty output: `{'h': 1, 'e': 1, 'l': 1, 'o': 1}`

**Ordinary passing input for faulty:** `all_unique`

**Reference correctness:** The reference correctly builds a dict by incrementing counts for each character seen

**Boundary cases checked:** empty, single_char

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m12 — invert_dict(d)

**Specification:** Return a new dictionary with keys and values of d swapped: each value v in d becomes a key in the result mapping to its original key. d is a Python dictionary with string keys and string values. Do not modify the input.

**Reference:**
```python
def invert_dict(d):
    result = {}
    for key in d:
        result[d[key]] = key
    return result
```

**Faulty:**
```python
def invert_dict(d):
    result = {}
    for key in d:
        result[key] = d[key]
    return result
```

**Named counterexample** (`swap_needed`, kind=ordinary):
- Input: `[{'a': 'x', 'b': 'y'}]`
- Expected: `{'x': 'a', 'y': 'b'}`
- Faulty output: `{'a': 'x', 'b': 'y'}`

**Ordinary passing input for faulty:** `identity_pairs`

**Reference correctness:** The reference correctly swaps keys and values by assigning result[d[key]] = key for each key

**Boundary cases checked:** empty_dict, single_identity

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m13 — merge_dicts(d1, d2)

**Specification:** Return a new dictionary merging d1 and d2. For keys present in both, the value is the sum of the two values. For keys in only one dictionary, use that value. d1 and d2 are Python dictionaries with integer values. Do not modify the inputs.

**Reference:**
```python
def merge_dicts(d1, d2):
    result = {}
    for key in d1:
        result[key] = d1[key]
    for key in d2:
        if key in result:
            result[key] += d2[key]
        else:
            result[key] = d2[key]
    return result
```

**Faulty:**
```python
def merge_dicts(d1, d2):
    result = {}
    for key in d1:
        result[key] = d1[key]
    for key in d2:
        result[key] = d2[key]
    return result
```

**Named counterexample** (`common_key_sum`, kind=ordinary):
- Input: `[{'a': 1, 'b': 2}, {'b': 3, 'c': 4}]`
- Expected: `{'a': 1, 'b': 5, 'c': 4}`
- Faulty output: `{'a': 1, 'b': 3, 'c': 4}`

**Ordinary passing input for faulty:** `no_common`

**Reference correctness:** The reference correctly copies d1 then sums d2 values for common keys

**Boundary cases checked:** both_empty, first_empty

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m14 — most_frequent(values)

**Specification:** Return the element that appears most often in values. If there is a tie, return the element that appears first in values. values is a non-empty Python list of integers (excluding bool). Do not modify the input.

**Reference:**
```python
def most_frequent(values):
    best = values[0]
    best_count = 0
    for v in values:
        count = 0
        for u in values:
            if u == v:
                count += 1
        if count > best_count:
            best_count = count
            best = v
    return best
```

**Faulty:**
```python
def most_frequent(values):
    best = values[0]
    best_count = 0
    for v in values:
        count = 0
        for u in values:
            if u == v:
                count += 1
        if count >= best_count:
            best_count = count
            best = v
    return best
```

**Named counterexample** (`tie_goes_first`, kind=adversarial):
- Input: `[[1, 2, 1, 2]]`
- Expected: `1`
- Faulty output: `2`

**Ordinary passing input for faulty:** `clear_winner`

**Reference correctness:** The reference correctly counts each element's frequency and tracks the first with the maximum count using strict >

**Boundary cases checked:** single, two_elements

**Findings:** no issue

### m15 — count_by_parity(values)

**Specification:** Return a dictionary with keys "even" and "odd" mapping to the count of even and odd integers in values, respectively. values is any Python list of integers (excluding bool), including an empty list. Do not modify the input.

**Reference:**
```python
def count_by_parity(values):
    result = {"even": 0, "odd": 0}
    for v in values:
        if v % 2 == 0:
            result["even"] += 1
        else:
            result["odd"] += 1
    return result
```

**Faulty:**
```python
def count_by_parity(values):
    result = {"even": 0, "odd": 0}
    for v in values:
        if v % 2 == 0:
            result["even"] += 1
        else:
            result["odd"] = 1
    return result
```

**Named counterexample** (`mixed`, kind=ordinary):
- Input: `[[1, 2, 3, 4, 5]]`
- Expected: `{'even': 2, 'odd': 3}`
- Faulty output: `{'even': 2, 'odd': 1}`

**Ordinary passing input for faulty:** `all_even`

**Reference correctness:** The reference correctly iterates over values and increments the even or odd counter based on parity

**Boundary cases checked:** empty, single_odd, single_even

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m16 — find_all_indices(values, target)

**Specification:** Return a list of all zero-based indices i where values[i] equals target, in ascending order. If target does not appear, return an empty list. values is any Python list of integers (excluding bool), including an empty list; target is an integer. Do not modify the input.

**Reference:**
```python
def find_all_indices(values, target):
    result = []
    for i in range(len(values)):
        if values[i] == target:
            result.append(i)
    return result
```

**Faulty:**
```python
def find_all_indices(values, target):
    result = []
    for i in range(len(values)):
        if values[i] == target:
            result.append(i)
            break
    return result
```

**Named counterexample** (`multiple_matches`, kind=ordinary):
- Input: `[[1, 2, 1, 2, 1], 1]`
- Expected: `[0, 2, 4]`
- Faulty output: `[0]`

**Ordinary passing input for faulty:** `single_match`

**Reference correctness:** The reference correctly collects all indices where the element equals the target

**Boundary cases checked:** empty, single_element_match

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m17 — binary_search(sorted_list, target)

**Specification:** Return the zero-based index of target in sorted_list using binary search, or -1 if target is absent. sorted_list is a Python list of integers sorted in non-decreasing order (excluding bool), including an empty list; target is an integer. Do not modify the input.

**Reference:**
```python
def binary_search(sorted_list, target):
    left = 0
    right = len(sorted_list) - 1
    while left <= right:
        mid = (left + right) // 2
        if sorted_list[mid] == target:
            return mid
        elif sorted_list[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
```

**Faulty:**
```python
def binary_search(sorted_list, target):
    left = 0
    right = len(sorted_list) - 1
    while left < right:
        mid = (left + right) // 2
        if sorted_list[mid] == target:
            return mid
        elif sorted_list[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
```

**Named counterexample** (`last_element`, kind=ordinary):
- Input: `[[1, 2, 3, 4, 5], 5]`
- Expected: `4`
- Faulty output: `-1`

**Ordinary passing input for faulty:** `middle_element`

**Reference correctness:** The reference correctly implements binary search with left <= right, checking the middle element

**Boundary cases checked:** empty, single_found, two_element_found

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m18 — first_above(values, threshold)

**Specification:** Return the smallest zero-based index i where values[i] is strictly greater than threshold, or -1 if no such element exists. values is any Python list of integers (excluding bool), including an empty list; threshold is an integer. Do not modify the input.

**Reference:**
```python
def first_above(values, threshold):
    for i in range(len(values)):
        if values[i] > threshold:
            return i
    return -1
```

**Faulty:**
```python
def first_above(values, threshold):
    for i in range(len(values)):
        if values[i] >= threshold:
            return i
    return -1
```

**Named counterexample** (`equals_threshold`, kind=ordinary):
- Input: `[[1, 3, 5, 7], 5]`
- Expected: `3`
- Faulty output: `2`

**Ordinary passing input for faulty:** `above_threshold`

**Reference correctness:** The reference correctly returns the first index where the element strictly exceeds the threshold

**Boundary cases checked:** empty, no_match, last_equals

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m19 — is_sorted(values)

**Specification:** Return True if values is sorted in non-decreasing order (each element is less than or equal to the next), otherwise False. values is any Python list of integers (excluding bool), including an empty list. An empty list and a single-element list are sorted. Do not modify the input.

**Reference:**
```python
def is_sorted(values):
    for i in range(len(values) - 1):
        if values[i] > values[i + 1]:
            return False
    return True
```

**Faulty:**
```python
def is_sorted(values):
    for i in range(len(values) - 1):
        if values[i] >= values[i + 1]:
            return False
    return True
```

**Named counterexample** (`with_duplicates`, kind=ordinary):
- Input: `[[1, 2, 2, 3]]`
- Expected: `True`
- Faulty output: `False`

**Ordinary passing input for faulty:** `strictly_increasing`

**Reference correctness:** The reference correctly checks that no element exceeds the next element (non-decreasing order)

**Boundary cases checked:** empty, single

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m20 — longest_run(values)

**Specification:** Return the length of the longest consecutive run of identical elements in values. A run is a maximal sequence of consecutive equal elements. values is any Python list of integers (excluding bool), including an empty list. For an empty list return 0. Do not modify the input.

**Reference:**
```python
def longest_run(values):
    if len(values) == 0:
        return 0
    longest = 1
    current = 1
    for i in range(1, len(values)):
        if values[i] == values[i - 1]:
            current += 1
        else:
            current = 1
        if current > longest:
            longest = current
    return longest
```

**Faulty:**
```python
def longest_run(values):
    if len(values) == 0:
        return 0
    longest = 1
    current = 1
    for i in range(1, len(values)):
        if values[i] == values[i - 1]:
            current += 1
        if current > longest:
            longest = current
    return longest
```

**Named counterexample** (`two_runs`, kind=ordinary):
- Input: `[[1, 1, 2, 2, 2]]`
- Expected: `3`
- Faulty output: `4`

**Ordinary passing input for faulty:** `all_same`

**Reference correctness:** The reference correctly tracks the current and longest run length, resetting current on mismatch

**Boundary cases checked:** empty, single

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m21 — power_of_two(n)

**Specification:** Return True if n is a positive integer power of 2 (1, 2, 4, 8, ...), otherwise False. n is any Python integer (excluding bool).

**Reference:**
```python
def power_of_two(n):
    if n < 1:
        return False
    while n > 1:
        if n % 2 != 0:
            return False
        n = n // 2
    return True
```

**Faulty:**
```python
def power_of_two(n):
    if n < 1:
        return False
    while n >= 1:
        if n % 2 != 0:
            return False
        n = n // 2
    return True
```

**Named counterexample** (`four`, kind=ordinary):
- Input: `[4]`
- Expected: `True`
- Faulty output: `False`

**Ordinary passing input for faulty:** `six`

**Reference correctness:** The reference correctly repeatedly divides by 2 and checks for remainders, returning True only if n reaches 1

**Boundary cases checked:** zero, one, negative

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m22 — ceil_div(a, b)

**Specification:** Return the ceiling of a divided by b: the smallest integer greater than or equal to a / b. a is a non-negative integer and b is a positive integer (both excluding bool).

**Reference:**
```python
def ceil_div(a, b):
    result = a // b
    if a % b != 0:
        result += 1
    return result
```

**Faulty:**
```python
def ceil_div(a, b):
    return a // b
```

**Named counterexample** (`remainder`, kind=ordinary):
- Input: `[7, 3]`
- Expected: `3`
- Faulty output: `2`

**Ordinary passing input for faulty:** `exact`

**Reference correctness:** The reference correctly computes floor division and adds 1 when there is a remainder

**Boundary cases checked:** one_one, same, small_numerator

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m23 — digit_sum(n)

**Specification:** Return the sum of the decimal digits of n. n is a non-negative integer (excluding bool). For n = 0 return 0.

**Reference:**
```python
def digit_sum(n):
    total = 0
    while n > 0:
        total += n % 10
        n = n // 10
    return total
```

**Faulty:**
```python
def digit_sum(n):
    total = 0
    while n > 1:
        total += n % 10
        n = n // 10
    return total
```

**Named counterexample** (`ones`, kind=ordinary):
- Input: `[11]`
- Expected: `2`
- Faulty output: `1`

**Ordinary passing input for faulty:** `two_digits`

**Reference correctness:** The reference correctly extracts digits with modulo 10 and accumulates them into a total

**Boundary cases checked:** zero, one

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m24 — count_digits(n)

**Specification:** Return the number of decimal digits in n. n is a non-negative integer (excluding bool). For n = 0 return 1.

**Reference:**
```python
def count_digits(n):
    if n == 0:
        return 1
    count = 0
    while n > 0:
        n = n // 10
        count += 1
    return count
```

**Faulty:**
```python
def count_digits(n):
    if n == 0:
        return 1
    count = 0
    while n > 1:
        n = n // 10
        count += 1
    return count
```

**Named counterexample** (`two_digits_msd1`, kind=ordinary):
- Input: `[11]`
- Expected: `2`
- Faulty output: `1`

**Ordinary passing input for faulty:** `two_digits_msd2`

**Reference correctness:** The reference correctly counts how many times n can be divided by 10 before reaching 0, with special case for n=0

**Boundary cases checked:** zero, one

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m25 — is_perfect_square(n)

**Specification:** Return True if n is a perfect square (there exists an integer k such that k * k equals n), otherwise False. n is any Python integer (excluding bool). Negative numbers are not perfect squares.

**Reference:**
```python
def is_perfect_square(n):
    if n < 0:
        return False
    k = 0
    while k * k < n:
        k += 1
    return k * k == n
```

**Faulty:**
```python
def is_perfect_square(n):
    if n < 0:
        return False
    k = 0
    while k * k <= n:
        k += 1
    return k * k == n
```

**Named counterexample** (`four`, kind=ordinary):
- Input: `[4]`
- Expected: `True`
- Faulty output: `False`

**Ordinary passing input for faulty:** `two`

**Reference correctness:** The reference correctly increments k until k*k >= n and checks for exact equality

**Boundary cases checked:** zero, one, negative

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m26 — is_anagram(s1, s2)

**Specification:** Return True if s1 and s2 are anagrams of each other (case-insensitive), otherwise False. Two strings are anagrams if they contain the same characters with the same frequencies, ignoring case. s1 and s2 are any Python strings.

**Reference:**
```python
def is_anagram(s1, s2):
    s1 = s1.lower()
    s2 = s2.lower()
    return sorted(s1) == sorted(s2)
```

**Faulty:**
```python
def is_anagram(s1, s2):
    return sorted(s1) == sorted(s2)
```

**Named counterexample** (`mixed_case`, kind=ordinary):
- Input: `['Abc', 'bca']`
- Expected: `True`
- Faulty output: `False`

**Ordinary passing input for faulty:** `same_case`

**Reference correctness:** The reference correctly lowercases both strings and compares their sorted character sequences

**Boundary cases checked:** both_empty, single_same

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m27 — kth_smallest(values, k)

**Specification:** Return the k-th smallest element of values (1-indexed: k=1 returns the minimum). values is a non-empty Python list of integers (excluding bool); k is a positive integer at most len(values). Do not modify the input.

**Reference:**
```python
def kth_smallest(values, k):
    sorted_list = sorted(values)
    return sorted_list[k - 1]
```

**Faulty:**
```python
def kth_smallest(values, k):
    sorted_list = sorted(values)
    return sorted_list[len(values) - k]
```

**Named counterexample** (`smallest`, kind=ordinary):
- Input: `[[3, 1, 4, 2], 1]`
- Expected: `1`
- Faulty output: `4`

**Ordinary passing input for faulty:** `symmetric`

**Reference correctness:** The reference correctly sorts the list and returns the element at index k-1 (1-indexed)

**Boundary cases checked:** single, middle_three

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m28 — has_duplicate(values)

**Specification:** Return True if values contains any duplicate element, otherwise False. values is any Python list of integers (excluding bool), including an empty list. Do not modify the input.

**Reference:**
```python
def has_duplicate(values):
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if values[i] == values[j]:
                return True
    return False
```

**Faulty:**
```python
def has_duplicate(values):
    for i in range(len(values)):
        for j in range(i + 2, len(values)):
            if values[i] == values[j]:
                return True
    return False
```

**Named counterexample** (`adjacent_dup`, kind=ordinary):
- Input: `[[1, 1]]`
- Expected: `True`
- Faulty output: `False`

**Ordinary passing input for faulty:** `non_adjacent_dup`

**Reference correctness:** The reference correctly compares every pair (i, j) with i < j for equality

**Boundary cases checked:** empty, single

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m29 — sorted_intersection(list1, list2)

**Specification:** Return a sorted list of the unique elements that appear in both list1 and list2. list1 and list2 are Python lists of integers (excluding bool). Do not modify the inputs.

**Reference:**
```python
def sorted_intersection(list1, list2):
    result = []
    for v in sorted(set(list1)):
        if v in list2:
            result.append(v)
    return result
```

**Faulty:**
```python
def sorted_intersection(list1, list2):
    result = []
    for v in sorted(list1):
        if v in list2:
            result.append(v)
    return result
```

**Named counterexample** (`dup_in_list1`, kind=ordinary):
- Input: `[[1, 2, 2, 3], [2, 3]]`
- Expected: `[2, 3]`
- Faulty output: `[2, 2, 3]`

**Ordinary passing input for faulty:** `no_dup_list1`

**Reference correctness:** The reference correctly iterates over sorted unique elements of list1 and checks membership in list2

**Boundary cases checked:** both_empty, single_match

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

### m30 — count_even_sum_pairs(values)

**Specification:** Return the number of pairs (i, j) with i < j such that values[i] + values[j] is even. values is any Python list of integers (excluding bool), including an empty list. Do not modify the input.

**Reference:**
```python
def count_even_sum_pairs(values):
    count = 0
    n = len(values)
    for i in range(n):
        for j in range(i + 1, n):
            if (values[i] + values[j]) % 2 == 0:
                count += 1
    return count
```

**Faulty:**
```python
def count_even_sum_pairs(values):
    count = 0
    n = len(values)
    for i in range(n):
        for j in range(i + 2, n):
            if (values[i] + values[j]) % 2 == 0:
                count += 1
    return count
```

**Named counterexample** (`adjacent_even`, kind=ordinary):
- Input: `[[1, 1]]`
- Expected: `1`
- Faulty output: `0`

**Ordinary passing input for faulty:** `non_adjacent_even`

**Reference correctness:** The reference correctly counts all pairs (i, j) with i < j whose sum is divisible by 2

**Boundary cases checked:** empty, single

**Findings:** no issue | design note: Counterexample is classified 'ordinary' (pilot used 'edge' for counterexamples)

## Oracle Method

Each task was verified using an independent oracle function that computes
expected values from first principles (Python built-ins, alternative
algorithms, or mathematical formulas), NOT by running the reference
solution. The oracle and the reference implementation are independent.

## Code Comment Scan

All reference and faulty solution code was scanned for comments and
docstrings containing revealing keywords (bug, fault, correct, wrong,
broken, fix, defect, error, reference, counterexample, intentional,
deliberate, planted). No revelations were found in any task.
