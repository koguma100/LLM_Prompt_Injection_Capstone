from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
import json


class PerformanceStats:
    def __init__(self, actuals, predicted):
        self.actuals = actuals
        self.predicted = predicted

    def confusion_matrix(self, filename="confusion_matrix.png"):
        cm = confusion_matrix(self.actuals, self.predicted)
        disp = ConfusionMatrixDisplay(confusion_matrix=cm)
        disp.plot(cmap='Blues', values_format='d')
        plt.title('Confusion Matrix')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"confusion matrix saved to {filename}")
        return cm

    def print_false_negatives(self, prompts: list[str], filename="false_negatives.txt"):
        false_negatives = [
            prompt for prompt, actual, pred in zip(prompts, self.actuals, self.predicted)
            if actual == 1 and pred == 0
        ]

        with open(filename, 'w') as f:
            f.write("False Negatives (actual=injection, predicted=benign):\n")
            f.write("=" * 30 + "\n")
            if not false_negatives:
                f.write("None found.\n")
            else:
                for i, prompt in enumerate(false_negatives, 1):
                    f.write(f"{i}. {prompt}\n")

        print(f"{len(false_negatives)} false negative(s) saved to {filename}")
        return false_negatives


    def stats(self, filename="performance_stats.txt"):
        stats = {
            'accuracy': accuracy_score(self.actuals, self.predicted),
            'precision': precision_score(self.actuals, self.predicted),
            'recall': recall_score(self.actuals, self.predicted),
            'f1_score': f1_score(self.actuals, self.predicted)
        }
        with open(filename, 'w') as f:
            f.write("Performance Statistics:\n")
            f.write("=" * 30 + "\n")
            f.write(f"Accuracy:  {stats['accuracy']:.4f}\n")
            f.write(f"Precision: {stats['precision']:.4f}\n")
            f.write(f"Recall:    {stats['recall']:.4f}\n")
            f.write(f"F1 Score:  {stats['f1_score']:.4f}\n")

        print(f"Statistics exported to {filename}")
        return stats