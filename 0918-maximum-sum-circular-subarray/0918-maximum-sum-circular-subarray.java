class Solution {
    public int kadens(int[] nums){
        int currSum = nums[0];
        int overAllSum = nums[0];

        for(int i = 1; i < nums.length ; i++){
            if(currSum + nums[i] > nums[i]){
                currSum += nums[i];
            }else currSum = nums[i];

            overAllSum = Math.max(currSum, overAllSum);
        }

        return overAllSum;
    }
    public int maxSubarraySumCircular(int[] nums) {
        int linearSum = kadens(nums);
        int totalSum = 0;
        for(int i = 0; i < nums.length; i++){
            totalSum += nums[i];
            nums[i] *= -1;
        }

        int invertedSum = kadens(nums);

        if(totalSum + invertedSum == 0) return linearSum;

        return Math.max(linearSum , totalSum + invertedSum);

    }
}