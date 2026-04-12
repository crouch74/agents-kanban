import { useState } from "react";

export function useDraftFormsState() {
  const [draftTaskTitle, setDraftTaskTitle] = useState("");
  const [draftRepoPath, setDraftRepoPath] = useState("");
  const [draftRepoName, setDraftRepoName] = useState("");
  const [draftWorktreeLabel, setDraftWorktreeLabel] = useState("");
  const [draftQuestionPrompt, setDraftQuestionPrompt] = useState("");
  const [draftQuestionReason, setDraftQuestionReason] = useState("");
  const [draftQuestionUrgency, setDraftQuestionUrgency] = useState("medium");
  const [draftReplyBody, setDraftReplyBody] = useState("");
  const [draftCommentBody, setDraftCommentBody] = useState("");
  const [draftCheckSummary, setDraftCheckSummary] = useState("");
  const [draftCheckType] = useState("verification");
  const [draftCheckStatus, setDraftCheckStatus] = useState("pending");
  const [draftArtifactName, setDraftArtifactName] = useState("");
  const [draftArtifactType] = useState("log");
  const [draftArtifactUri, setDraftArtifactUri] = useState("");
  const [draftSubtaskTitle, setDraftSubtaskTitle] = useState("");

  return {
    draftTaskTitle,
    setDraftTaskTitle,
    draftRepoPath,
    setDraftRepoPath,
    draftRepoName,
    setDraftRepoName,
    draftWorktreeLabel,
    setDraftWorktreeLabel,
    draftQuestionPrompt,
    setDraftQuestionPrompt,
    draftQuestionReason,
    setDraftQuestionReason,
    draftQuestionUrgency,
    setDraftQuestionUrgency,
    draftReplyBody,
    setDraftReplyBody,
    draftCommentBody,
    setDraftCommentBody,
    draftCheckSummary,
    setDraftCheckSummary,
    draftCheckType,
    draftCheckStatus,
    setDraftCheckStatus,
    draftArtifactName,
    setDraftArtifactName,
    draftArtifactType,
    draftArtifactUri,
    setDraftArtifactUri,
    draftSubtaskTitle,
    setDraftSubtaskTitle,
  };
}
