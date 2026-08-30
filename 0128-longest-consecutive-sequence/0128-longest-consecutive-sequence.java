class Solution {
    public int longestConsecutive(int[] nums) {
        if(nums.length == 0) return 0;
        Arrays.sort(nums);
        int lastSmaller = Integer.MIN_VALUE;
        int currCount = 0;
        int largest = 1;

        for(int i = 0 ; i < nums.length; i++){
            if(nums[i] - 1 == lastSmaller){
                currCount++;
                lastSmaller = nums[i];
            }else if(lastSmaller != nums[i]){
                currCount = 1;
                lastSmaller = nums[i];
            }
            largest = Math.max(largest, currCount);
        }
        return largest;

    }
}