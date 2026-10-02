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
        print(f"Detection confusion matrix saved to {filename}")
        return cm

    # Output validation fail rate of the LLM response before vs. after sanitization, split by label.
    # Malicious: the after rate should drop (injections neutralized). Benign: both rates should stay near 0 (no over-redaction).
    def sanitization_fail_rates(self, unsanitized_valid, sanitized_valid, filename="sanitization_fail_rates.png"):
        columns = ["Label", "Samples", "Failed validation\nbefore sanitization", "Failed validation\nafter sanitization", "Change"]
        rows = []
        for name, label in (("Malicious", 1), ("Benign", 0)):
            idx = [i for i, actual in enumerate(self.actuals) if actual == label]
            n = len(idx)
            before = sum(1 for i in idx if not unsanitized_valid[i])
            after = sum(1 for i in idx if not sanitized_valid[i])
            before_pct = 100 * before / n if n else 0
            after_pct = 100 * after / n if n else 0
            rows.append([name, str(n), f"{before}/{n} ({before_pct:.0f}%)", f"{after}/{n} ({after_pct:.0f}%)",
                         f"{after_pct - before_pct:+.0f} pts"])

        fig, ax = plt.subplots(figsize=(10, 1.8))
        ax.axis("off")
        table = ax.table(cellText=rows, colLabels=columns, cellLoc="center", loc="center",
                         colWidths=[0.14, 0.12, 0.28, 0.28, 0.14])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2.2)
        for (row, _), cell in table.get_celld().items():
            cell.set_edgecolor("#d0cfca")
            if row == 0:
                cell.set_facecolor("#eef3fb")
                cell.set_text_props(weight="bold")
        ax.set_title("Output Validation Fail Rate Before vs. After Sanitization", weight="bold")
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()

        print("\nSANITIZATION EFFECTIVENESS (responses failing output validation)")
        print(f"{'Label':<10}{'Samples':>8}{'Before sanitization':>22}{'After sanitization':>21}{'Change':>11}")
        for row in rows:
            print(f"{row[0]:<10}{row[1]:>8}{row[2]:>22}{row[3]:>21}{row[4]:>11}")
        print(f"Sanitization effectiveness table saved to {filename}")
        return rows

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

        print(f"{len(false_negatives)} false negative(s) (injection predicted as benign) saved to {filename}")
        return false_negatives

    def print_false_positives(self, prompts: list[str], filename="false_positives.txt"):
        false_positives = [
            prompt for prompt, actual, pred in zip(prompts, self.actuals, self.predicted)
            if actual == 0 and pred == 1
        ]

        with open(filename, 'w') as f:
            f.write("False Positives (actual=injection, predicted=benign):\n")
            f.write("=" * 30 + "\n")
            if not false_positives:
                f.write("None found.\n")
            else:
                for i, prompt in enumerate(false_positives, 1):
                    f.write(f"{i}. {prompt}\n")

        print(f"{len(false_positives)} false positive(s) (benign predicted as injection) saved to {filename}")
        return false_positives


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

        print(f"Detection performance stats (accuracy, precision, recall, F1) saved to {filename}")
        return stats