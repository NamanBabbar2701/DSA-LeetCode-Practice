class Solution {
    public List<List<Integer>> threeSum(int[] nums) {
        List<List<Integer>> ans = new ArrayList<>();
        Arrays.sort(nums);
        for(int i = 0 ; i < nums.length ; i++){
            if(i > 0 && nums[i - 1] == nums[i]){
                continue;
            }
            List<List<Integer>> pair = twoSum(nums, i+1 , nums.length-1 , -nums[i]);

            for(List<Integer> trip : pair){
                trip.add(0, nums[i]);
                ans.add(trip);
            }
        }
        return ans;        
    }

    public List<List<Integer>> twoSum(int[] nums , int l , int r, int target){
        List<List<Integer>> res = new ArrayList<>();

        int start = l;
        while(l < r){
            if(l > start && nums[l-1] == nums[l]){
                l++;
                continue;
            }

            int sum = nums[l] + nums[r];

            if(sum == target){
                List<Integer> pair = new ArrayList<>();
                pair.add(nums[l]);
                pair.add(nums[r]);
                res.add(pair);
                l++;
                r--;
            }else if(sum > target){
                r--;
            }else l++;
        } 
        return res;
    }
}