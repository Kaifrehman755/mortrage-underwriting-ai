import { apiClient } from "@/lib/api";
import { MOCK_APPLICATIONS } from "@/lib/mockData";
import { UnderwritingDocument, ExtractedField, ValidationIssue, DocumentType } from "@/types";

export const documentService = {
  async getDocumentsByApplication(applicationId?: string): Promise<UnderwritingDocument[]> {
    try {
      return await apiClient<UnderwritingDocument[]>(`/documents?application_id=${applicationId || ""}`);
    } catch {
      const app = applicationId
        ? MOCK_APPLICATIONS.find((a) => a.id === applicationId)
        : MOCK_APPLICATIONS[0];
      return app ? app.documents : MOCK_APPLICATIONS[0].documents;
    }
  },

  async getAllDocuments(): Promise<UnderwritingDocument[]> {
    try {
      return await apiClient<UnderwritingDocument[]>("/documents");
    } catch {
      return MOCK_APPLICATIONS.flatMap((a) => a.documents);
    }
  },

  async getExtractedFields(applicationId?: string): Promise<ExtractedField[]> {
    try {
      return await apiClient<ExtractedField[]>(`/documents/extraction?application_id=${applicationId || ""}`);
    } catch {
      const app = applicationId
        ? MOCK_APPLICATIONS.find((a) => a.id === applicationId)
        : MOCK_APPLICATIONS[0];
      return app ? app.extractedFields : MOCK_APPLICATIONS[0].extractedFields;
    }
  },

  async getValidationIssues(applicationId?: string): Promise<ValidationIssue[]> {
    try {
      return await apiClient<ValidationIssue[]>(`/documents/validation?application_id=${applicationId || ""}`);
    } catch {
      const app = applicationId
        ? MOCK_APPLICATIONS.find((a) => a.id === applicationId)
        : MOCK_APPLICATIONS[0];
      return app ? app.validationIssues : MOCK_APPLICATIONS[0].validationIssues;
    }
  },

  async uploadDocument(
    file: File,
    docType: DocumentType,
    applicationId: string
  ): Promise<UnderwritingDocument> {
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("document_type", docType);
      formData.append("application_id", applicationId);

      return await apiClient<UnderwritingDocument>("/documents/upload", {
        method: "POST",
        body: formData,
      });
    } catch {
      // Demo adapter: generate mock uploaded document
      const newDoc: UnderwritingDocument = {
        id: `DOC-${Date.now().toString().slice(-6)}`,
        applicationId: applicationId || "APP-2026-0841",
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type || "application/pdf",
        documentType: docType,
        uploadedAt: new Date().toISOString(),
        processingStatus: "Validated",
        ocrConfidence: 97.5,
        extractedFieldCount: 12,
        validationIssueCount: 0,
        sha256Hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      };

      const app = MOCK_APPLICATIONS.find((a) => a.id === applicationId) || MOCK_APPLICATIONS[0];
      app.documents.push(newDoc);
      return newDoc;
    }
  },

  async updateExtractedField(
    fieldId: string,
    newValue: string | number,
    note?: string
  ): Promise<ExtractedField> {
    try {
      return await apiClient<ExtractedField>(`/documents/extraction/${fieldId}`, {
        method: "PATCH",
        body: JSON.stringify({ normalizedValue: newValue, underwriterNote: note }),
      });
    } catch {
      for (const app of MOCK_APPLICATIONS) {
        const field = app.extractedFields.find((f) => f.id === fieldId);
        if (field) {
          field.normalizedValue = newValue;
          field.validationStatus = "Edited";
          field.underwriterNote = note || "Manually adjusted by underwriter.";
          return field;
        }
      }
      throw new Error("Field not found");
    }
  },
};
