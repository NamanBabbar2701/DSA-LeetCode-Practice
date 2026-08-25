class Solution {
    public int maxProfit(int[] prices) {
        int minVal = prices[0];
        int maxProfit = 0;
        int i = 1;
        while(i < prices.length){
            maxProfit = Math.max(maxProfit , prices[i] - minVal);
            i++;
            minVal = Math.min(minVal, prices[i-1]);
        }       
        return maxProfit;
    }
}