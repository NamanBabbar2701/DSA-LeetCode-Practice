class Solution {
    public int maxOperations(int[] nums, int k) {
        int l = 0 ,  r = nums.length - 1;
        Arrays.sort(nums);
        int opCount = 0;
        while(l < r){
            if(nums[l] + nums[r] == k){
                opCount++;
                l++;
                r--;
            }else if(nums[l] + nums[r] > k){
                r--;
            }else l++;
        }
        return opCount;
    }
}