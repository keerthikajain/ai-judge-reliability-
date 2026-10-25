# Main Study Review Sheet

Generated: 2026-10-22T05:39:38.126805+00:00

All human-review statuses are pending. No API calls were made.

| ID | Category | Function | Bug Summary | Counterexample | Ordinary Pass |
|-----|----------|----------|-------------|----------------|---------------|
| m01 | string processing | `count_vowels(s)` | The faulty solution checks ch against lowercase vowels only, so uppercase vowels... | uppercase_vowels | yes |
| m02 | string processing | `is_palindrome(s)` | The faulty solution omits the lower() call, so characters differing only in case... | mixed_case_palindrome | yes |
| m03 | string processing | `count_occurrences(s, c)` | The faulty solution assigns 1 instead of incrementing, so it returns at most 1 f... | two_occurrences | yes |
| m04 | string processing | `uppercase_first(s)` | The faulty solution lowercases the remainder of the string, destroying uppercase... | mixed_case_rest | yes |
| m05 | string processing | `replace_char(s, old, new)` | The faulty solution appends old instead of new when a match is found, leaving th... | replace_l | yes |
| m06 | list transformations | `double_all(values)` | The faulty solution adds 2 instead of multiplying by 2, which only produces the ... | simple_values | yes |
| m07 | list transformations | `interleave(list1, list2)` | The faulty solution appends the list2 element before the list1 element at each s... | distinct_values | yes |
| m08 | list transformations | `sum_list(values)` | The faulty solution iterates over values[1:] instead of values, omitting the fir... | skip_first | yes |
| m09 | list transformations | `cumulative_sum(values)` | The faulty solution appends the current value v instead of the running total, re... | simple | yes |
| m10 | list transformations | `rotate_left(values, k)` | The faulty solution uses (i + k) % n instead of (i - k) % n, rotating right inst... | rotate_one | yes |
| m11 | dictionary/counting operations | `char_frequency(s)` | The faulty solution sets the count to 1 instead of incrementing when a character... | with_repeats | yes |
| m12 | dictionary/counting operations | `invert_dict(d)` | The faulty solution copies key-value pairs unchanged instead of swapping them, r... | swap_needed | yes |
| m13 | dictionary/counting operations | `merge_dicts(d1, d2)` | The faulty solution overwrites d1 values with d2 values for common keys instead ... | common_key_sum | yes |
| m14 | dictionary/counting operations | `most_frequent(values)` | The faulty solution uses >= instead of > for comparison, so ties are resolved in... | tie_goes_first | yes |
| m15 | dictionary/counting operations | `count_by_parity(values)` | The faulty solution assigns 1 instead of incrementing for the odd count, so any ... | mixed | yes |
| m16 | searching and index handling | `find_all_indices(values, target)` | The faulty solution breaks after the first match, returning only the first index... | multiple_matches | yes |
| m17 | searching and index handling | `binary_search(sorted_list, target)` | The faulty solution uses left < right instead of left <= right, so the loop exit... | last_element | yes |
| m18 | searching and index handling | `first_above(values, threshold)` | The faulty solution uses >= instead of >, so it returns the index of an element ... | equals_threshold | yes |
| m19 | searching and index handling | `is_sorted(values)` | The faulty solution uses >= instead of >, rejecting lists with equal adjacent el... | with_duplicates | yes |
| m20 | searching and index handling | `longest_run(values)` | The faulty solution omits the else branch that resets current to 1, so the runni... | two_runs | yes |
| m21 | integer arithmetic and boundaries | `power_of_two(n)` | The faulty solution uses while n >= 1 instead of while n > 1, so the loop contin... | four | yes |
| m22 | integer arithmetic and boundaries | `ceil_div(a, b)` | The faulty solution returns the floor division result without adding 1 when ther... | remainder | yes |
| m23 | integer arithmetic and boundaries | `digit_sum(n)` | The faulty solution uses while n > 1 instead of while n > 0, so the loop exits b... | ones | yes |
| m24 | integer arithmetic and boundaries | `count_digits(n)` | The faulty solution uses while n > 1 instead of while n > 0, so the loop exits o... | two_digits_msd1 | yes |
| m25 | integer arithmetic and boundaries | `is_perfect_square(n)` | The faulty solution uses k * k <= n instead of k * k < n, so k overshoots the sq... | four | yes |
| m26 | small algorithms | `is_anagram(s1, s2)` | The faulty solution omits the lower() calls on both strings, so characters diffe... | mixed_case | yes |
| m27 | small algorithms | `kth_smallest(values, k)` | The faulty solution returns sorted_list[len(values) - k] (the k-th largest) inst... | smallest | yes |
| m28 | small algorithms | `has_duplicate(values)` | The faulty solution uses range(i + 2, ...) instead of range(i + 1, ...), so adja... | adjacent_dup | yes |
| m29 | small algorithms | `sorted_intersection(list1, list2)` | The faulty solution iterates over sorted(list1) instead of sorted(set(list1)), s... | dup_in_list1 | yes |
| m30 | small algorithms | `count_even_sum_pairs(values)` | The faulty solution uses range(i + 2, n) instead of range(i + 1, n), so adjacent... | adjacent_even | yes |

## By Category

### dictionary/counting operations

**m11**: `char_frequency(s)`
- Spec: Return a dictionary mapping each character in s to the number of times it appears. s is any Python string, including an empty string. For an empty string return an empty dictionary.
- Bug: The faulty solution sets the count to 1 instead of incrementing when a character is already present, so repeated characters always show a count of 1.
- Counterexample: with_repeats
- Tests: 8 cases

**m12**: `invert_dict(d)`
- Spec: Return a new dictionary with keys and values of d swapped: each value v in d becomes a key in the result mapping to its original key. When multiple original keys share the same value, the last key encountered in dictionary iteration order wins in the inverted result. d is a Python dictionary with string keys and string values. Do not modify the input.
- Bug: The faulty solution copies key-value pairs unchanged instead of swapping them, returning the original dictionary.
- Counterexample: swap_needed
- Tests: 9 cases

**m13**: `merge_dicts(d1, d2)`
- Spec: Return a new dictionary merging d1 and d2. For keys present in both, the value is the sum of the two values. For keys in only one dictionary, use that value. d1 and d2 are Python dictionaries with integer values. Do not modify the inputs.
- Bug: The faulty solution overwrites d1 values with d2 values for common keys instead of summing them.
- Counterexample: common_key_sum
- Tests: 8 cases

**m14**: `most_frequent(values)`
- Spec: Return the element that appears most often in values. If there is a tie, return the element that appears first in values. values is a non-empty Python list of integers (excluding bool). Do not modify the input.
- Bug: The faulty solution uses >= instead of > for comparison, so ties are resolved in favor of the last occurrence rather than the first.
- Counterexample: tie_goes_first
- Tests: 8 cases

**m15**: `count_by_parity(values)`
- Spec: Return a dictionary with keys "even" and "odd" mapping to the count of even and odd integers in values, respectively. values is any Python list of integers (excluding bool), including an empty list. Do not modify the input.
- Bug: The faulty solution assigns 1 instead of incrementing for the odd count, so any list with odd numbers reports at most 1 odd.
- Counterexample: mixed
- Tests: 8 cases


### integer arithmetic and boundaries

**m21**: `power_of_two(n)`
- Spec: Return True if n is a positive integer power of 2 (1, 2, 4, 8, ...), otherwise False. n is any Python integer (excluding bool).
- Bug: The faulty solution uses while n >= 1 instead of while n > 1, so the loop continues when n reaches 1 and returns False for all powers of 2.
- Counterexample: four
- Tests: 8 cases

**m22**: `ceil_div(a, b)`
- Spec: Return the ceiling of a divided by b: the smallest integer greater than or equal to a / b. a is a non-negative integer and b is a positive integer (both excluding bool).
- Bug: The faulty solution returns the floor division result without adding 1 when there is a remainder.
- Counterexample: remainder
- Tests: 8 cases

**m23**: `digit_sum(n)`
- Spec: Return the sum of the decimal digits of n. n is a non-negative integer (excluding bool). For n = 0 return 0.
- Bug: The faulty solution uses while n > 1 instead of while n > 0, so the loop exits before processing the final digit when it equals 1.
- Counterexample: ones
- Tests: 8 cases

**m24**: `count_digits(n)`
- Spec: Return the number of decimal digits in n. n is a non-negative integer (excluding bool). For n = 0 return 1.
- Bug: The faulty solution uses while n > 1 instead of while n > 0, so the loop exits one iteration early when n reaches 1, undercounting by 1.
- Counterexample: two_digits_msd1
- Tests: 8 cases

**m25**: `is_perfect_square(n)`
- Spec: Return True if n is a perfect square (there exists an integer k such that k * k equals n), otherwise False. n is any Python integer (excluding bool). Negative numbers are not perfect squares.
- Bug: The faulty solution uses k * k <= n instead of k * k < n, so k overshoots the square root and the final equality check always fails for perfect squares.
- Counterexample: four
- Tests: 8 cases


### list transformations

**m06**: `double_all(values)`
- Spec: Return a new list where each element of values is multiplied by 2. values is any Python list of integers (excluding bool), including an empty list. Do not modify the input.
- Bug: The faulty solution adds 2 instead of multiplying by 2, which only produces the correct result when v equals 2.
- Counterexample: simple_values
- Tests: 8 cases

**m07**: `interleave(list1, list2)`
- Spec: Return a new list interleaving elements of list1 and list2, taking one element from list1 then one from list2, in order. Both lists have the same length. list1 and list2 are Python lists of integers. Do not modify the inputs.
- Bug: The faulty solution appends the list2 element before the list1 element at each step, reversing the required interleaving order.
- Counterexample: distinct_values
- Tests: 8 cases

**m08**: `sum_list(values)`
- Spec: Return the sum of all integers in values. values is any Python list of integers (excluding bool), including an empty list. For an empty list return 0. Do not modify the input.
- Bug: The faulty solution iterates over values[1:] instead of values, omitting the first element from the sum.
- Counterexample: skip_first
- Tests: 8 cases

**m09**: `cumulative_sum(values)`
- Spec: Return a new list of cumulative sums of values: the i-th element is the sum of values[0] through values[i]. values is any Python list of integers (excluding bool), including an empty list. For an empty list return an empty list. Do not modify the input.
- Bug: The faulty solution appends the current value v instead of the running total, returning the original list instead of cumulative sums.
- Counterexample: simple
- Tests: 8 cases

**m10**: `rotate_left(values, k)`
- Spec: Return a new list with the elements of values rotated left by k positions. A left rotation by k moves each element k positions toward the front, wrapping around. values is a Python list of integers (excluding bool); k is a non-negative integer. For an empty list return an empty list. Do not modify the input.
- Bug: The faulty solution uses (i + k) % n instead of (i - k) % n, rotating right instead of left.
- Counterexample: rotate_one
- Tests: 8 cases


### searching and index handling

**m16**: `find_all_indices(values, target)`
- Spec: Return a list of all zero-based indices i where values[i] equals target, in ascending order. If target does not appear, return an empty list. values is any Python list of integers (excluding bool), including an empty list; target is an integer. Do not modify the input.
- Bug: The faulty solution breaks after the first match, returning only the first index instead of all indices.
- Counterexample: multiple_matches
- Tests: 8 cases

**m17**: `binary_search(sorted_list, target)`
- Spec: Return the zero-based index of target in sorted_list using binary search, or -1 if target is absent. When the list contains duplicate elements equal to target, any index pointing to target is a valid result. sorted_list is a Python list of integers sorted in non-decreasing order (excluding bool), including an empty list; target is an integer. Do not modify the input.
- Bug: The faulty solution uses left < right instead of left <= right, so the loop exits without checking the element when left equals right.
- Counterexample: last_element
- Tests: 9 cases

**m18**: `first_above(values, threshold)`
- Spec: Return the smallest zero-based index i where values[i] is strictly greater than threshold, or -1 if no such element exists. values is any Python list of integers (excluding bool), including an empty list; threshold is an integer. Do not modify the input.
- Bug: The faulty solution uses >= instead of >, so it returns the index of an element equal to the threshold rather than strictly above it.
- Counterexample: equals_threshold
- Tests: 8 cases

**m19**: `is_sorted(values)`
- Spec: Return True if values is sorted in non-decreasing order (each element is less than or equal to the next), otherwise False. values is any Python list of integers (excluding bool), including an empty list. An empty list and a single-element list are sorted. Do not modify the input.
- Bug: The faulty solution uses >= instead of >, rejecting lists with equal adjacent elements that are still sorted in non-decreasing order.
- Counterexample: with_duplicates
- Tests: 8 cases

**m20**: `longest_run(values)`
- Spec: Return the length of the longest consecutive run of identical elements in values. A run is a maximal sequence of consecutive equal elements. values is any Python list of integers (excluding bool), including an empty list. For an empty list return 0. Do not modify the input.
- Bug: The faulty solution omits the else branch that resets current to 1, so the running count never resets between different runs.
- Counterexample: two_runs
- Tests: 8 cases


### small algorithms

**m26**: `is_anagram(s1, s2)`
- Spec: Return True if s1 and s2 are anagrams of each other (case-insensitive), otherwise False. Both strings are lowercased using str.lower() before comparison. Two strings are anagrams if they contain the same characters with the same frequencies. s1 and s2 are any Python strings.
- Bug: The faulty solution omits the lower() calls on both strings, so characters differing only in case are treated as different.
- Counterexample: mixed_case
- Tests: 9 cases

**m27**: `kth_smallest(values, k)`
- Spec: Return the k-th smallest element of values (1-indexed: k=1 returns the minimum). values is a non-empty Python list of integers (excluding bool); k is a positive integer at most len(values). Do not modify the input.
- Bug: The faulty solution returns sorted_list[len(values) - k] (the k-th largest) instead of sorted_list[k - 1] (the k-th smallest).
- Counterexample: smallest
- Tests: 8 cases

**m28**: `has_duplicate(values)`
- Spec: Return True if values contains any duplicate element, otherwise False. values is any Python list of integers (excluding bool), including an empty list. Do not modify the input.
- Bug: The faulty solution uses range(i + 2, ...) instead of range(i + 1, ...), so adjacent elements are never compared and adjacent duplicates are missed.
- Counterexample: adjacent_dup
- Tests: 8 cases

**m29**: `sorted_intersection(list1, list2)`
- Spec: Return a sorted list of the unique elements that appear in both list1 and list2. list1 and list2 are Python lists of integers (excluding bool). Do not modify the inputs.
- Bug: The faulty solution iterates over sorted(list1) instead of sorted(set(list1)), so duplicate elements in list1 that are also in list2 appear multiple times in the result.
- Counterexample: dup_in_list1
- Tests: 8 cases

**m30**: `count_even_sum_pairs(values)`
- Spec: Return the number of pairs (i, j) with i < j such that values[i] + values[j] is even. values is any Python list of integers (excluding bool), including an empty list. Do not modify the input.
- Bug: The faulty solution uses range(i + 2, n) instead of range(i + 1, n), so adjacent pairs (j = i + 1) are never checked.
- Counterexample: adjacent_even
- Tests: 8 cases


### string processing

**m01**: `count_vowels(s)`
- Spec: Return the number of vowels (a, e, i, o, u) in string s, counted case-insensitively. Case-insensitivity is applied by calling str.lower() on each character before checking membership in the vowel set. s is any Python string, including an empty string.
- Bug: The faulty solution checks ch against lowercase vowels only, so uppercase vowels like E and O are not counted.
- Counterexample: uppercase_vowels
- Tests: 9 cases

**m02**: `is_palindrome(s)`
- Spec: Return True if s is a palindrome (reads the same forwards and backwards), case-insensitively. The entire string is lowercased using str.lower() before comparison. s is any Python string, including an empty string.
- Bug: The faulty solution omits the lower() call, so characters differing only in case are treated as different.
- Counterexample: mixed_case_palindrome
- Tests: 9 cases

**m03**: `count_occurrences(s, c)`
- Spec: Return the number of times character c appears in string s. s is any Python string (including empty); c is a single character string.
- Bug: The faulty solution assigns 1 instead of incrementing, so it returns at most 1 for any count above zero.
- Counterexample: two_occurrences
- Tests: 8 cases

**m04**: `uppercase_first(s)`
- Spec: Return a copy of s with the first character uppercased and all remaining characters unchanged. If s is empty, return the empty string. s is any Python string.
- Bug: The faulty solution lowercases the remainder of the string, destroying uppercase characters after the first position.
- Counterexample: mixed_case_rest
- Tests: 8 cases

**m05**: `replace_char(s, old, new)`
- Spec: Return a copy of s where every occurrence of character old is replaced with character new. Characters not equal to old are left unchanged. s is any Python string; old and new are single character strings.
- Bug: The faulty solution appends old instead of new when a match is found, leaving the string unchanged.
- Counterexample: replace_l
- Tests: 8 cases
