class Solution {
    public void setZeroes(int[][] matrix) {
        int[] rowArray = new int[matrix.length];
        int[] columnArray = new int[matrix[0].length];
        for (int i = 0; i < matrix.length; i++) {
            for (int j = 0; j < matrix[0].length; j++) {
                if (matrix[i][j] == 0) {
                    rowArray[i] = 1;
                    columnArray[j] = 1;
                }
            }
        }

        for (int i = 0; i < matrix.length; i++) {
            for (int j = 0; j < matrix[0].length; j++) {
                if (rowArray[i] == 1 || columnArray[j] == 1) {
                    matrix[i][j] = 0;
                }
            }
        }

    }
}