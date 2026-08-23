class Solution {
    public int kadens(int[] nums){
      int currentSum = nums[0];
        int overallSum = nums[0];

        for(int i = 1 ; i < nums.length; i++){
            if(currentSum + nums[i] > nums[i]){
                currentSum += nums[i];
            }else currentSum = nums[i];

            overallSum = Math.max(currentSum , overallSum);
        }

        return overallSum;  
    }
    public int maxSubarraySumCircular(int[] nums) {
        if(nums.length == 0) return 0;
        // int currentSum1 = nums[0];
        // int overallSum1 = nums[0];

        // for(int i = 1 ; i < nums.length; i++){
        //     if(currentSum1 + nums[i] > nums[i]){
        //         currentSum1 += nums[i];
        //     }else currentSum1 = nums[i];

        //     overallSum1 = Math.max(currentSum1 , overallSum1);
        // }
        int linearSum = kadens(nums);
        
        int totalSum = 0;
        for(int i = 0 ; i < nums.length ; i++){
            totalSum += nums[i];
            nums[i] *= -1;
        }

        // 
        int invertedSum = kadens(nums);

        if(totalSum + invertedSum == 0) return linearSum;

        return Math.max(linearSum, totalSum + invertedSum);
    }
}